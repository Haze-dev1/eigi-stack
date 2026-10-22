# LRN profile — local stack and accounts

The filled-in instance of the six-line profile in `SKILL.md` step 0, for LRN. Another project copies this shape and replaces every value.

Everything runs on non-default ports so it never collides with a developer's own servers on 8000/3000. Each block assumes the variables from §1 are still set; if your shell does not keep state between commands, re-export them in each one.

| Piece | Port | Started by |
|---|---|---|
| MongoDB 7 (single-node replica set; transactions need it) | 27027 | §1 |
| API (uvicorn) | 8765 | §3 |
| Frontend (`next dev`) | 3765 | §4 |

## 1. Workspace and MongoDB

```bash
REPO=$(git rev-parse --show-toplevel)
W=$(mktemp -d)                       # empty dir: no .env is loaded from here
SKILL_DIR=${SKILL_DIR:-~/.claude/skills/eigi-test}   # the dir holding this skill's SKILL.md
export MONGODB_URI="mongodb://localhost:27027/?directConnection=true"
export JWT_SECRET="lrn-test-local-$(date +%s)-0123456789abcdef"   # made up for this run; settings require >= 32 characters
export PYTHONPATH="$REPO/backend"

docker run -d --rm --name lrn-test-mongo -p 27027:27017 mongo:7 --replSet rs0 --bind_ip_all
until docker exec lrn-test-mongo mongosh --quiet --eval 'db.runCommand({ping:1}).ok' 2>/dev/null | grep -q 1; do sleep 1; done
docker exec lrn-test-mongo mongosh --quiet --eval 'rs.initiate({_id:"rs0",members:[{_id:0,host:"localhost:27017"}]}).ok'
sleep 3   # let the node become primary
```

## 2. Live-database tests

Run the whole backend suite from `$W` so the Mongo-gated tests join the rest. The allowed target must equal `host:port/database` exactly; the tests refuse to run otherwise.

```bash
cd "$W" && MONGODB_DATABASE=lrn_it RUN_MONGO_INTEGRATION_TESTS=1 \
  MONGO_INTEGRATION_TEST_ALLOWED_TARGET=localhost:27027/lrn_it \
  "$REPO/backend/.venv/bin/python" -m pytest -q -rs -p no:cacheprovider \
  -c "$REPO/backend/pyproject.toml" --rootdir "$REPO/backend" "$REPO/backend/tests"
```

## 3. API and accounts

```bash
export MONGODB_DATABASE="lrn_test_$(date +%s)"
cd "$W" && "$REPO/backend/.venv/bin/python" "$SKILL_DIR/scripts/seed_users.py" > "$W/users.json"

cd "$W"   # separate line: with `cd && cmd &`, $! would be a wrapper shell, not uvicorn
APP_ENV=development FRONTEND_ORIGIN=http://localhost:3765 COOKIE_SECURE=false \
  EIGI_BASE_URL=http://127.0.0.1:9 \
  nohup "$REPO/backend/.venv/bin/python" -m uvicorn main:app --app-dir "$REPO/backend" --port 8765 \
  > "$W/api.log" 2>&1 & echo $! > "$W/api.pid"
until curl -sf localhost:8765/health >/dev/null; do sleep 1; done
```

- `users.json` holds `[{role, email, user_id, token}]`: two students (for cross-account checks) and a superadmin. Pass `role:email` arguments to the seed script for others. Institution admins come from the real path: a student requests an institution in onboarding and the superadmin approves it.
- Call the API with `curl -H "Authorization: Bearer $TOKEN" localhost:8765/v1/...`. Sanity check: `/v1/account` returns 200 with a student token, 401 without one, and `/v1/admin/schools` returns 403 for a student.
- Application logs go to `$W/logs/debug.log` (the logger writes to `logs/` under the working directory). `$W/api.log` only has uvicorn output.
- Outage mode is the default above. For a provider-backed check the user has budgeted, restart the API without the `EIGI_BASE_URL` override and with the provider variables passed explicitly; count the calls in `debug.log` against the budget.

## 4. Frontend

```bash
cd "$REPO/frontend"
git status --short next-env.d.ts   # note whether it was already modified
NEXT_PUBLIC_API_BASE_URL=http://localhost:8765 nohup npx next dev -p 3765 > "$W/web.log" 2>&1 & echo $! > "$W/web.pid"
until curl -s -o /dev/null -w '%{http_code}' localhost:3765/signin | grep -q 200; do sleep 2; done
```

Sign in by setting `localStorage.lrn_access_token` to a token from `users.json` on `http://localhost:3765`, then reloading. The theme is `localStorage["lrn-theme"]` = `light` or `dark`.

## 5. Teardown

```bash
kill "$(cat "$W/web.pid")" "$(cat "$W/api.pid")" 2>/dev/null
sleep 2
for port in 8765 3765; do   # npx leaves a next-server child; free the run's ports by listener PID
  pid=$(ss -ltnpH "sport = :$port" | grep -oP 'pid=\K[0-9]+' | head -1)
  [ -n "$pid" ] && kill "$pid"
done
docker stop lrn-test-mongo            # --rm removes the container and its data
cd "$REPO" && git checkout -- frontend/next-env.d.ts   # only if §4 found it unmodified: next dev rewrites it
git status --short                    # only the files the user expects should show
```

Copy any screenshots or logs the report cites out of `$W` before deleting it.

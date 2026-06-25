# TODO: Connect Existing Profile UI with Backend

## Step 1
Implement `/api/profile` (GET/PUT) in `src/app/api/profile/route.ts`.
- GET: decode JWT, load user from MongoDB
- PUT: validate + update user fields (name, email, mobile, companyName)

## Step 2
Wire the existing `ProfileModal` to the backend.
- On open: fetch profile and replace hardcoded values
- On Save: call update endpoint and then refresh displayed values

## Step 3 (only if required)
Update `src/modules/auth/user.model.ts` to add optional `companyName` field.
- Keep backward compatibility

## Step 4
Run typecheck/dev server to ensure no TS/Next errors.


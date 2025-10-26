# 1. Fix all models
python fix_all_jsonb.py

# 2. Delete ALL old migrations
rm migrations/versions/*.py

# 3. Delete database
rm *.db

# 4. Create fresh migration
alembic revision --autogenerate -m "Initial migration"

# 5. Check the migration file for any JSONB (should be none)
grep -n "JSONB" migrations/versions/*.py

# 6. If clean, run migration
alembic upgrade head
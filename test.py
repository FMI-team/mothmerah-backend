# 1. Fix all models (remove JSONB, fix UUID imports)
python3 fix_all_jsonb.py
python3 fix_uuid_imports.py

# 2. Delete ALL old migrations
rm -f migrations/versions/*.py

# 3. Delete database
rm -f *.db

# 4. Create fresh migration
alembic revision --autogenerate -m "Initial migration"

# 5. Fix migration for SQLite (remove CheckConstraints with regex, fix autoincrement)
python3 fix_migration_for_sqlite.py

# 6. Check the migration file for any JSONB (should be none)
grep -n "JSONB" migrations/versions/*.py || echo "✅ No JSONB found"
grep -n "CheckConstraint.*~" migrations/versions/*.py || echo "✅ No regex CheckConstraints found"

# 7. Run migration
alembic upgrade head

# 8. Run seed
python3 seed_db.py
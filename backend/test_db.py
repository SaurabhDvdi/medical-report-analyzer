import os
os.environ['PYTHONUNBUFFERED'] = '1'
try:
    from database import engine, DATABASE_URL
    print(f'Connection URL: {DATABASE_URL[:60]}...')
    conn = engine.connect()
    print('✓ MySQL connection successful!')
    conn.close()
except Exception as e:
    print(f'❌ Error: {type(e).__name__}')
    print(f'Message: {str(e)[:300]}')

from server import *
import os

if not os.path.isfile('db.sqlite3'):
    db.create_all()
    print('Creating Database')
else:
    print('Database already exist')
    print('Continue?')
    ans = input('[Y/N]')
    
    if ans.lower() == 'y':
        db.create_all()
        print('Creating Database')
        exit()
    elif ans.lower() == 'n':
        print('Ok... Closing')
        exit()
    else:
        print('nigger')
    
    
    
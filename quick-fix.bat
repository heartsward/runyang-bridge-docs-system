@echo off
cd backend
call venv\Scripts\activate.bat
pip install email-validator PyJWT python-jose[cryptography] passlib[bcrypt] python-multipart alembic pydantic-settings pydantic[email]
call venv\Scripts\deactivate.bat
echo Fixed! Try start-services.bat now
pause
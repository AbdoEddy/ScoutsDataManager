# Local Setup Guide for Scout Management Application

This guide will walk you through setting up and running the Scout Management application on your local machine.

## Prerequisites

1. Python 3.10 or 3.11 installed on your computer
2. pip (Python package manager)
3. Git (optional, for cloning)
4. PostgreSQL database (optional - SQLite can be used for testing)

## Step 1: Get the Code

### Option 1: Download from Replit
1. Click the three dots (⋮) in the Replit file browser
2. Select "Download as zip"
3. Extract the ZIP file to a folder on your computer

### Option 2: Export via Git
If Replit supports Git export, you can use that option to download the code.

## Step 2: Set Up a Virtual Environment

```bash
# Navigate to the project directory
cd path/to/scout-management

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

## Step 3: Install Dependencies

The project includes a `requirements_list.txt` file. Rename this to `requirements.txt` and install the dependencies:

```bash
# Rename the file
mv requirements_list.txt requirements.txt

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

1. The project includes a `.env.example` file. Make a copy and rename it to `.env`:

```bash
cp .env.example .env
```

2. Edit the `.env` file with your settings:
   - For PostgreSQL, update the database connection string
   - For SQLite (simpler), uncomment the SQLite line and comment out PostgreSQL
   - Generate a secure session key (you can use the command below):

```python
python -c "import secrets; print(secrets.token_hex(16))"
```

3. Replace the `SESSION_SECRET` value in your `.env` file with this generated key.

## Step 5: Initialize the Database

The project includes an `init_db.py` script to set up your database:

```bash
python init_db.py
```

This will:
1. Create all database tables
2. Create a default admin user (username: admin, password: admin123)
3. Set up any default tables defined in the application

## Step 6: Run the Application

You have two options to run the application:

### Option 1: Using the included run script

```bash
python run_local.py
```

### Option 2: Using Flask directly

```bash
# Set Flask environment variables
export FLASK_APP=main.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# On Windows CMD:
# set FLASK_APP=main.py
# set FLASK_ENV=development
# set FLASK_DEBUG=1

# Run Flask
flask run --host=0.0.0.0 --port=5000
```

### Option 3: Using Gunicorn (Linux/Mac only, more production-like)

```bash
gunicorn --bind 0.0.0.0:5000 "main:app"
```

## Step 7: Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

Log in with the default admin credentials:
- Username: admin
- Password: admin123

## Troubleshooting Common Issues

### Database Connection Problems
- For PostgreSQL:
  - Ensure PostgreSQL service is running on your machine
  - Verify username/password are correct in `.env`
  - Check that the database exists
- For SQLite:
  - Ensure the application has write permissions to create the database file

### Package Installation Issues
- Try installing problematic packages individually:
  ```bash
  pip install package-name
  ```
- Ensure you're using a compatible Python version (3.10-3.11)

### Port Already in Use
- Change the port in run commands (e.g., `--port=5001`)
- Check what's using port 5000:
  ```bash
  # On Linux/Mac:
  lsof -i :5000
  # On Windows:
  netstat -ano | findstr :5000
  ```

### Permission Issues
- Ensure you have proper permissions for the project directory
- On Linux/Mac, you might need to use `sudo` for certain operations

## Next Steps

1. Change the default admin password immediately after first login
2. Add your organization's specific tables and fields
3. Create additional user accounts with appropriate roles
4. Back up your database regularly

## Production Deployment Considerations
For production deployment, additional steps would be needed:
- Use a production web server (Nginx/Apache)
- Set up proper TLS/SSL for secure HTTPS connections
- Configure a production database with backups
- Implement monitoring and logging

**Important:** For any production deployment, consult with IT security personnel to ensure the application meets security requirements.
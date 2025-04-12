# EManage
EManage is a management platform developed for COSC 4353.

## Technologies
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

## Getting Started ##
The management system requires the MySQL DBMS. The latest version may be found [here](https://www.mysql.com/downloads/).

1. **Clone the repository:**

   ```sh
   git clone https://github.com/ParkerTraxler/EManage.git
   cd EManage
   ```

2. **Setup:**

   ```sh
   pip install -r requirements.txt
   ```

3. **Configuration:**
   The software will read system environment variables or a .env file (in that order) to configure the application.\\
   You must create an app registration in Azure to be able to create user accounts with Office365 accounts, which you can use to set these variables:

   ```sh
   CLIENT_ID='your_client_id'
   CLIENT_SECRET='your_client_secret'
   AUTHORITY='your_authority_url'
   REDIRECT_URI='your_redirect_uri'
   ```

   You must also specify a secret key for signing session data:

   ```sh
   SECRET_KEY='your_secret_key'
   ```

   And finally, the database URI:

   ```sh
   DATABASE_URI='your_database_uri'
   ```

4. **Starting the app:**

   ```sh
   python run.py
   ```

   The app by default will run on port 5000.

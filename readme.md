# FileKeeper

FileKeeper is a web application built using Quart and SQLite that allows users to upload and manage their files securely. It includes features like user registration, login, file upload, and a progress bar to track file upload progress.

## Features

- User registration and login: Users can create an account and log in securely.
- File upload: Users can upload files to the server and manage them.
- Progress bar: A progress bar is displayed during file upload to show the upload progress.
- File management: Users can view and manage their uploaded files.

## Requirements

- Python 3.8 or later
- Quart web framework
- aiosqlite library
- hashlib library
- SQLite database

## Installation

1. Clone the repository:

```bash
git clone https://github.com/fossyy/FileKeeper.git
cd FileKeeper
```

2. Install the required dependencies:

```bash
git clone pip install -r requirements.txt
```

3. Run the application:

```bash
python app.py
```
The application should now be running at http://localhost:5000/

## Usage
1. Access the application in your web browser at http://localhost:5000/.
2. If you are a new user, click on the "Register" link to create an account. If you already have an account, click on the "Login" link to log in.
3. After logging in, you can upload files using the "File Upload" form.
4. The progress bar will show the upload progress, and once the upload is complete, the file will be saved on the server.
5. You can view and manage your uploaded files on the homepage.
6. To log out, click on the "Logout" link.

## Inspiration
This project was inspired by the upload progress bar implementation found on CodePen: https://codepen.io/PerfectIsShit/pen/zogMXP. The progress bar implementation allows users to track the file upload progress.

## Contributing
Contributions are welcome! If you find any bugs or have suggestions for improvements, please feel free to open an issue or submit a pull request.

## Author
Bagas - https://github.com/fossyy

import base64

import yaml
import bcrypt
import jwt

users_config_file = "./config/users.yaml"
global_config_file = "./config/global.yaml"


class User:
    username: str
    encoded_password: str
    role: str

    def __init__(self, d: dict):
        self.username = d.get('username')
        self.encoded_password = d.get('password')
        self.role = d.get('role')

    def to_dict(self) -> dict:
        return {"username": self.username, "password": self.encoded_password, "role": self.role}

    def get_auth_token(self) -> str:
        return jwt.encode(
            {
                "username": self.username,
                "role": self.role
            },
            yaml.safe_load(open(global_config_file, 'r'))['jwt_key'], "HS256"
        )

    def check_pwd(self, password) -> bool:
        return bcrypt.checkpw(password.encode('UTF-8'), string_to_bytes(self.encoded_password))


def bytes_to_string(value: bytes) -> str:
    return base64.b64encode(value).decode('UTF-8')


def string_to_bytes(value: str) -> bytes:
    return base64.b64decode(value.encode('UTF-8'))


def is_admin(user_cookie: str) -> bool:
    user = authenticate(user_cookie)
    if user and user.role == 'admin':
        return True
    return False


def create_user(username: str, password: str, role: str, user_cookie: str):
    users = load_users()
    if len(users) > 0 and not is_admin(user_cookie):
        print("Unauthorized attempt to create account")
        return
    salt = bcrypt.gensalt()
    password_encoded = bcrypt.hashpw(password.encode('utf-8'), salt)
    new_users_list = [user for user in users if user.username != username]
    new_user = User(
        {
            "username": username,
            "password": bytes_to_string(password_encoded),
            "role": role
        }
    )
    new_users_list.append(new_user)
    save_users(new_users_list)
    return new_user


def authenticate(jwt_token: str) -> User:
    if jwt_token and len(jwt_token) > 0:
        cookie_user = jwt.decode(jwt_token.encode('UTF-8'), yaml.safe_load(open(global_config_file, 'r'))['jwt_key'], "HS256")
        if cookie_user:
            users = load_users()
            for user in users:
                if user.username == cookie_user['username']:
                    return user


def user_login(username, password) -> User:
    users = load_users()
    for user in users:
        if user.username == username:
            if user.check_pwd(password):
                return user


def save_users(users: list[User]):
    yaml.dump({"users": [user.to_dict() for user in users]}, open(users_config_file, 'w'))


def load_users() -> list[User]:
    config = yaml.safe_load(open(users_config_file, 'r'))
    if config and 'users' in config and (isinstance(config['users'], list) or isinstance(config['users'], dict)) :
        return [User(user_data) for user_data in config['users']]
    return []


if __name__ == "__main__":
    print("Please use the web interface to discover and manage cameras.")
    print("Run 'python web_app.py' to start the web interface.")

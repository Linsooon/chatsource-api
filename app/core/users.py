import uuid
from typing import Optional

from fastapi import Depends, Request, BackgroundTasks
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from httpx_oauth.clients.google import GoogleOAuth2

from app.core.db import User, get_user_db
from app.core.config import settings
from app.core.mailer import simple_send, send_in_background, EmailSchema
from starlette.responses import JSONResponse

SECRET = "SECRET"

google_oauth_client = GoogleOAuth2(
    settings.GOOGLE_CLIENT_ID,
    settings.GOOGLE_CLIENT_SECRET,
)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self,
                                user: User,
                                request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(self,
                                       user: User,
                                       token: str,
                                       request: Optional[Request] = None):
        print(
            f"User {user.id} has forgot their password. Reset token: {token}")
        #res = await request.json()
        test_email = EmailSchema(email=[user.email])
        await simple_send(test_email)
        return JSONResponse(status_code=200, content={"message": "email has been sent"})
        

    async def on_after_request_verify(self,
                                      user: User,
                                      token: str,
                                      request: Optional[Request] = None):
        print(
            f"Verification requested for user {user.id}. Verification token: {token}"
        )


async def get_user_manager(
        user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)

from dataclasses import Field
from typing import Optional
from uuid import UUID

import boto3
import phonenumbers
from botocore.config import Config
from pydantic import BaseModel, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber


class CognitoUser(BaseModel):
    sub: UUID
    email: EmailStr
    email_verified: bool
    name: str
    phone_number: Optional[PhoneNumber]
    company: Optional[str]
    department: Optional[str]


class CreateCognitoUserIn(BaseModel):
    name: str
    email: EmailStr
    phone_number: Optional[PhoneNumber] = None
    company: Optional[str] = None
    department: Optional[str] = None

    @property
    def attribute_list(self) -> list[dict]:
        attributes = [
            {"Name": "email", "Value": self.email},
            {"Name": "name", "Value": self.name},
            {"Name": "email_verified", "Value": "true"},
        ]
        if self.phone_number is not None:
            attributes.append(
                {
                    "Name": "phone_number",
                    "Value": phonenumbers.format_number(
                        phonenumbers.parse(self.phone_number),
                        phonenumbers.PhoneNumberFormat.E164,
                    ),
                }
            )
        if self.company is not None:
            attributes.append({"Name": "custom:company", "Value": self.company})
        if self.department is not None:
            attributes.append({"Name": "custom:department", "Value": self.department})
        return attributes


class PatchCognitoUserIn(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[PhoneNumber] = Field(
        default=None, examples=["+821012345678"]
    )
    company: Optional[str] = None
    department: Optional[str] = None

    @property
    def attribute_list(self) -> list[dict]:
        attributes = []
        if self.name is not None:
            attributes.append({"Name": "name", "Value": self.name})
        if self.phone_number is not None:
            attributes.append(
                {
                    "Name": "phone_number",
                    "Value": phonenumbers.format_number(
                        phonenumbers.parse(self.phone_number),
                        phonenumbers.PhoneNumberFormat.E164,
                    ),
                }
            )
        if self.company is not None:
            attributes.append({"Name": "custom:company", "Value": self.company})
        if self.department is not None:
            attributes.append({"Name": "custom:department", "Value": self.department})
        return attributes


class CognitoSettings:
    access_key_id: str
    secret_access_key: str
    region: str
    cognito_user_pool_id: str


class CognitoAPI:
    def __init__(self):
        self.settings = CognitoSettings()
        self._boto3_session = boto3.Session(
            aws_access_key_id=self.settings.access_key_id,
            aws_secret_access_key=self.settings.secret_access_key,
            region_name=self.settings.region,
        )
        self._client = self._boto3_session.client(
            "cognito-idp",
            config=Config(
                retries={"max_attempts": 5, "mode": "standard"},
                connect_timeout=5,
                read_timeout=10,
            ),
        )

    def _response_user_to_cognito_user(
        self, user: dict, attributes_key: str
    ) -> CognitoUser:
        sub = ""
        email = ""
        email_verified = False
        name = ""
        company = ""
        phone_number = ""
        department = ""
        for attribute in user[attributes_key]:
            if attribute["Name"] == "email":
                email = attribute["Value"]
            elif attribute["Name"] == "email_verified":
                email_verified = attribute["Value"] == "true"
            elif attribute["Name"] == "name":
                name = attribute["Value"]
            elif attribute["Name"] == "custom:company":
                company = attribute["Value"]
            elif attribute["Name"] == "sub":
                sub = attribute["Value"]
            elif attribute["Name"] == "phone_number":
                phone_number = attribute["Value"]
            elif attribute["Name"] == "custom:department":
                department = attribute["Value"]

        return CognitoUser(
            sub=UUID(sub),
            email=email,
            email_verified=email_verified,
            name=name,
            phone_number=phone_number if phone_number else None,
            company=company if company else None,
            department=department if department else None,
        )

    def get_user(self, username: UUID) -> Optional[CognitoUser]:
        try:
            response = self._client.admin_get_user(
                UserPoolId=self.settings.cognito_user_pool_id,
                Username=str(username),
            )
            user = self._response_user_to_cognito_user(
                response, attributes_key="UserAttributes"
            )
            return user
        except Exception:
            return None

    def get_all_user_list(self) -> list[CognitoUser]:
        all_users: list[dict] = []
        paginator = self._client.get_paginator("list_users")
        page_iterator = paginator.paginate(
            UserPoolId=self.settings.cognito_user_pool_id
        )
        for page in page_iterator:
            all_users.extend(page["Users"])

        return [
            self._response_user_to_cognito_user(user, attributes_key="Attributes")
            for user in all_users
        ]

    def add_user(self, create_cognito_user_in: CreateCognitoUserIn) -> CognitoUser:
        response = self._client.admin_create_user(
            UserPoolId=self.settings.cognito_user_pool_id,
            Username=create_cognito_user_in.email,
            UserAttributes=create_cognito_user_in.attribute_list,
            DesiredDeliveryMediums=["EMAIL"],
        )
        return self._response_user_to_cognito_user(
            response["User"], attributes_key="Attributes"
        )

    def delete_user(self, sub: UUID) -> None:
        try:
            self._client.admin_delete_user(
                UserPoolId=self.settings.cognito_user_pool_id,
                Username=str(sub),
            )
        except Exception as e:
            raise Exception(f"Failed to delete user: {e}")

    def patch_user(
        self, sub: UUID, patch_cognito_user_in: PatchCognitoUserIn
    ) -> CognitoUser:
        self._client.admin_update_user_attributes(
            UserPoolId=self.settings.cognito_user_pool_id,
            Username=str(sub),
            UserAttributes=patch_cognito_user_in.attribute_list,
        )
        return self.get_user(username=sub)

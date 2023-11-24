import asyncio

import aiohttp
import requests
import time

from fastapi import Form
from pydantic import BaseModel


class Pet(BaseModel):
    userId: int
    petId: int
    name: str
    type: str
    breed: str
    age: int
    healthRecords: str
    createdAt: str


class Microservices:

    def __init__(self, access_token: str):
        self.headers = {"Authorization": f"Bearer {access_token}"}

    def get_adoption_query(self, adoption):
        pet_id = adoption['petId']
        adopt_user_id = adoption['adopterId']
        adopt_email = self.get_user_sync(int(adopt_user_id))['email']

        pet = self.get_pet_sync(int(pet_id))
        pet_name = pet['name']
        shel_user_id = pet['userid']
        shel_email = self.get_user_sync(int(shel_user_id))['email']

        query = {"adoption_id": adoption['adoptionId'],
                 "adopter_email": adopt_email,
                 "shelter_email": shel_email,
                 "pet_name": pet_name}
        return query

    async def get_user(self, user_id):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            start_time = time.time()
            async with session.get(
                    f"https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/users/{user_id}",
                    headers=self.headers) as response:
                user = await response.json()
                end_time = time.time()
                print(f"User Async returned in {end_time - start_time: 2f} seconds")
                return user

    async def get_pet(self, pet_id):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            start_time = time.time()
            async with session.get(
                    f"https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/pets/{pet_id}",
                    headers=self.headers) as response:
                pet = await response.json()
                end_time = time.time()
                print(f"Pet Async returned in {end_time - start_time: 2f} seconds")
                return pet

    @staticmethod
    async def get_adoption(adoption_id):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            start_time = time.time()
            async with session.get(f"http://18.217.19.86/adoptions/{adoption_id}") as response:
                adoption = await response.json()
                end_time = time.time()
                print(f"Get adoption Async returned in {end_time - start_time: 2f} seconds")
                return adoption

    @staticmethod
    async def delete_adoption(adoption_id):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            start_time = time.time()
            async with session.delete(f"http://18.217.19.86/adoptions/{adoption_id}",
                                      params={"adoption_id": adoption_id}) as response:
                await response.json()
                result = response.status
                end_time = time.time()
                print(f"Delete adoption Async returned in {end_time - start_time: 2f} seconds")
                return result

    @staticmethod
    async def deny_adoption(adoption_id, query, data):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            start_time = time.time()
            async with session.put(f"http://18.217.19.86/adoptions/{adoption_id}", params=query, json=data) as response:
                adoption = await response.json()
                end_time = time.time()
                print(f"Adoption Async returned in {end_time - start_time: 2f} seconds")
                return response.status

    async def apply_for_adoption_async(self, user_id: str, pet_id: str) -> dict:
        adoption_data = {
            "adopterId": user_id,
            "petId": pet_id
        }

        url_create_adoption = "http://18.217.19.86/adoptions"

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.post(url_create_adoption, json=adoption_data) as response_create_adoption:
                if response_create_adoption.status in {200, 201}:  # Assuming 201 means successful creation
                    created_adoption = await response_create_adoption.json()
                else:
                    return {"error": f"Failed to create adoption. Status code: {response_create_adoption.status}"}

        user_info = requests.get(
            f"https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/users/{user_id}",
            headers=self.headers).json()

        url_update_adoption = f"http://18.217.19.86/adoptions/{created_adoption['adoptionId']}"

        pending_payload = {
            "status": "pending"
        }

        query = self.get_adoption_query(created_adoption)
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.put(url_update_adoption, params=query, json=pending_payload) as response_update_adoption:
                if response_update_adoption.status in {200, 201}:  # Assuming 200 means successful update
                    updated_adoption = await response_update_adoption.json()
                    return updated_adoption
                else:
                    return {
                        "error": f"Failed to update adoption with user information. "
                                 f"Status code: {response_update_adoption.status}"}

    async def create_pet_async(self, pet_data: Pet):
        url = "https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/pets"
        data = aiohttp.FormData()
        data.add_field('userId', pet_data.userId)
        data.add_field('petId', pet_data.petId)
        data.add_field('name', repr(pet_data.name))
        data.add_field('type', repr(pet_data.type))
        data.add_field('breed', repr(pet_data.breed))
        data.add_field('age', repr(pet_data.age))
        data.add_field('healthRecords', repr(pet_data.healthRecords))
        data.add_field('createdAt', repr(pet_data.createdAt))

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.post(url, headers=self.headers, data=data) as response:
                return await response.text()

    async def accept_adoption_async(self, adoption_id):
        accept_payload = {
            "status": "approved"
        }

        reject_payload = {
            "status": "rejected"
        }

        url = f"http://18.217.19.86/adoptions/{adoption_id}"
        adoption = self.get_adoption_sync(adoption_id)
        query = self.get_adoption_query(adoption)
        pet_id = adoption['petId']
        adopt_user_id = adoption['adopterId']

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.put(url, params=query, json=accept_payload) as response:
                if response.status == 200 or response.status == 201:
                    adoption_ids = [
                        adoption["adoptionId"]
                        for adoption in self.get_adoption_all()
                        if adoption["petId"] == str(pet_id) and adoption["adopterId"] != str(adopt_user_id)
                    ]

                    deny_responses = await asyncio.gather(
                        *(
                            self.deny_adoption(adop_id, {
                                **query,
                                "adoption_id": adop_id
                            }, reject_payload) for adop_id in adoption_ids
                        )
                    )

                    for dr in deny_responses:
                        if dr not in {200, 201}:
                            return {"error": f"Failed to deny adoption. Status code: {dr}"}
                    return {"success": "accept one and deny all"}
                else:
                    return {"error": f"Failed to accept adoption. Status code: {response.status}"}

    async def delete_pet_with_adoption_async(self, pet_id):
        response = requests.delete(f"https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/pets/{pet_id}",
                                   headers=self.headers)
        if response.status_code in {200, 201}:
            adoptions = self.get_adoption_all()
            delete_responses = await asyncio.gather(
                *(
                    self.delete_adoption(adop['adoptionId'])
                    for adop in adoptions if str(pet_id) == adop['petId']
                )
            )
            for dr in delete_responses:
                if dr not in {200, 201}:
                    return {"error": f"Failed to delete adoption. Status code: {dr}"}
            return {"success": "Pet and associated adoptions deleted"}
        else:
            return {"error": f"Failed to delete pet. Status code: {response.status_code}"}

    def get_pet_sync(self, pet_id):
        response = requests.get(f"https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/pets/{pet_id}",
                                headers=self.headers)
        print(f"Pet Sync returned")
        return response.json()

    def get_user_sync(self, user_id):
        response = requests.get(f"https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/users/{user_id}",
                                headers=self.headers)
        print(f"User Sync returned")
        return response.json()

    @staticmethod
    def get_adoption_sync(adoption_id):
        response = requests.get(f"http://18.217.19.86/adoptions/{adoption_id}")
        print(f"Adoption Sync returned")
        return response.json()

    def get_pet_all(self):
        response = requests.get(f"https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/pets",
                                headers=self.headers)
        return response.json()

    def get_pet_desc(self, pet_id):
        response = requests.get(
            f"https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/pets/{pet_id}/description",
            headers=self.headers)
        return response.json()

    @staticmethod
    def get_adoption_all():
        response = requests.get("http://18.217.19.86/adoptions")
        return response.json()

    def delete_user_and_pets_sync(self, user_id: int):
        user_info = self.get_user_sync(user_id)

        if not user_info:
            return {"error": "User not found"}

        url_user = f"https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/users/{user_id}"
        response_user = requests.delete(url_user, headers=self.headers)

        if response_user.status_code not in {200, 204}:
            return {"error": f"Failed to delete user. Status code: {response_user.status_code}"}

        for pet in (requests.get(f"https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/pets",
                                 headers=self.headers)).json():
            pet_id = pet["petid"]
            url_pet = f"https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/pets/{pet_id}"
            response_pet = requests.delete(url_pet, headers=self.headers)

            if response_pet.status_code not in {200, 204}:
                return {"error": f"Failed to delete pet {pet_id}. Status code: {response_pet.status_code}"}

        return {"message": f"User {user_id} and associated pets deleted successfully"}

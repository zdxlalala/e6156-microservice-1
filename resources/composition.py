import aiohttp
import requests
import time

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
                print(f"Adoption Async returned in {end_time - start_time: 2f} seconds")
                return adoption

    async def apply_for_adoption_async(self, user_id: int, pet_id: int) -> dict:
        adoption_data = {
            "petId": pet_id,
            "adopterId": user_id,
        }

        url_create_adoption = "http://18.217.19.86/adoptions"

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.post(url_create_adoption, json=adoption_data) as response_create_adoption:
                if response_create_adoption.status in {200, 201}:  # Assuming 201 means successful creation
                    created_adoption = await response_create_adoption.json()
                else:
                    return {"error": f"Failed to create adoption. Status code: {response_create_adoption.status}"}

        user_info = requests.get(
            f"http://https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/users/{user_id}",
            headers=self.headers).json()

        url_update_adoption = f"http://18.217.19.86/adoptions/{created_adoption['adoptionId']}"

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.put(url_update_adoption, json={"adopter_email": user_info['email']}) as response_update_adoption:
                if response_update_adoption.status in {200, 201}:  # Assuming 200 means successful update
                    updated_adoption = await response_update_adoption.json()
                    return updated_adoption
                else:
                    return {
                        "error": f"Failed to update adoption with user information. "
                                 f"Status code: {response_update_adoption.status}"}

    async def create_pet_async(self, pet_data: Pet):
        url = "https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/pets"
        data = f"userId={pet_data.userId}&petId={pet_data.petId}&name='{pet_data.name}'&type='{pet_data.type}'&breed='{pet_data.breed}'&age={pet_data.age}&healthRecords='{pet_data.healthRecords}'&createdAt='{pet_data.createdAt}'"
        print(data)
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.post(url, data=data, headers=self.headers) as response:

                return await response.json()

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
        response = requests.get(f"https://20t8y8ccj8.execute-api.us-east-2.amazonaws.com/Stage1/api/pets/{pet_id}/description",
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


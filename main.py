from fastapi import FastAPI, Response, HTTPException, Request, Form

# I like to launch directly and not use the standard FastAPI startup
import uvicorn
import asyncio
from pydantic import BaseModel
from resources.composition import Microservices
from resources.students import StudentsResource
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhdXRob3JpemVkVXNlciIsIm5hbWUiOiJRV1pNWC1VU0VSIiwiaWF0IjoxNzAwMjAxNzg3LCJleHAiOjE3MzYyMDE3ODd9.VFT_fTxwn_Qn3AGq6BUMcJamz3c2IuYA4nBa5oflkv8"

class Pet(BaseModel):
    userId: int
    petId: int
    name: str
    type: str
    breed: str
    age: int
    healthRecords: str
    createdAt: str


class User(BaseModel):
    user_id: int

class Adoption(BaseModel):
    adoption_id: int

class AdoptionApplication(BaseModel):
    pet_id: int
    user_id: int

class Listing(BaseModel):
    pet_name: str
    pet_type: str
    pet_breed: str
    pet_age: int
    pet_health_records: str
    #pet_description: str
    user_name: str
    user_email: str


class CompositeResource:

    def __init__(self):
        self.microservices = Microservices(token)

    async def get_composite_info(self, pet_id, user_id, adoption_id):
        pet_info = await self.microservices.get_pet(pet_id)
        user_info = await self.microservices.get_user(user_id)
        adoption_info = await self.microservices.get_adoption(adoption_id)

        async_sample = {
            "pet_info_async": pet_info,
            "user_info_async": user_info,
            "adoption_info_async": adoption_info
        }

        return async_sample

    def get_composite_info_sync(self, pet_id, user_id, adoption_id):
        pet_info = self.microservices.get_pet_sync(pet_id)
        user_info = self.microservices.get_user_sync(user_id)
        adoption_info = self.microservices.get_adoption_sync(adoption_id)

        sync_sample = {
            "pet_info": pet_info,
            "user_info": user_info,
            "adoption_info": adoption_info
        }

        return sync_sample


composite_resource = CompositeResource()
microservices = Microservices(token)
students_resource = StudentsResource()


# Synchronous implementation


@app.delete("/delete_user/{user_id}")
def delete_user(user_id: int):
    return microservices.delete_user_and_pets_sync(user_id)


@app.get("/composite_info_sync/{pet_id}/{user_id}/{adoption_id}")
def get_composite_info_sync(pet_id: int, user_id: int, adoption_id: str):
    result = composite_resource.get_composite_info_sync(pet_id, user_id, adoption_id)
    return result


# Asynchronous implementation

@app.post("/apply_for_adoption")
async def apply_for_adoption(adoption_data: AdoptionApplication):
    try:
        result = await microservices.apply_for_adoption_async(
            user_id=adoption_data.user_id,
            pet_id=adoption_data.pet_id
        )
        return result
    except Exception as e:
        # Handle exceptions or errors as needed
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/all_listings")
async def get_all_listings():
    pets = microservices.get_pet_all()
    all_listings = {}
    index = 1
    for pet in pets:
        user_info = await microservices.get_user(pet['userid'])
        all_listings[index] = Listing(pet_name=pet['name'],
                                      pet_type=pet['type'],
                                      pet_breed=pet['breed'],
                                      pet_age=pet['age'],
                                      pet_health_records=pet['healthrecords'],
                                      #pet_description=microservices.get_pet_desc(pet['petid']),
                                      user_name=user_info['username'],
                                      user_email=user_info['email']).model_dump()
        index += 1

    return all_listings


@app.post("/create_listing")
async def create_pet(pet_data: Pet):
    try:
        result = await microservices.create_pet_async(pet_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/user_detail/{user_id}")
async def user_and_pets_sync(user_id: int):
    user_info = await microservices.get_user(user_id)
    all_pets = microservices.get_pet_all()
    all_adoptions = microservices.get_adoption_all()

    pets = {}
    index = 1
    for p in all_pets:
        if p['userid'] == user_id:
            pets[index] = p
            index += 1

    adoptions = {}
    index = 1
    for adop in all_adoptions:
        if adop['adopterId'] == str(user_id):
            adoptions[index] = adop
            index += 1

    user_page = {
        "user_info": user_info,
        "listing_info": pets,
        "adoption_info": adoptions
    }

    return user_page


@app.put("/accept_adoption/{adoption_id}")
async def accept_adoption(adoption_id: str):
    try:
        result = await microservices.accept_adoption_async(adoption_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/composite_async/{user_id}/{pet_id}/{adoption_id}")
async def composite_async(user_id: int, pet_id: int, adoption_id: str):
    result = composite_resource.get_composite_info(user_id, pet_id, adoption_id)

    return await result


@app.get("/multiple_users_async/{user_ids}")
async def multiple_users_async(user_ids: str):
    user_ids_list = user_ids.split(',')

    async def get_user_info(user_id):
        return await microservices.get_user(user_id)

    users_info = await asyncio.gather(*(get_user_info(user_id) for user_id in user_ids_list))

    composite_resource = {
        "users_info": users_info
    }

    return composite_resource


@app.get("/batch_pet_adoption_status_async")
async def batch_pet_adoption_status_async(pet_ids: str):
    pet_ids_list = pet_ids.split(',')

    async def get_adoption_status(pet_id):
        return await microservices.get_adoption(pet_id)

    adoption_status = await asyncio.gather(*(get_adoption_status(pet_id) for pet_id in pet_ids_list))

    composite_resource = {
        "adoption_status": adoption_status
    }

    return composite_resource




@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Awesome cloud developer dz2510 says hello {name}"}


@app.get("/hello_text/{name}")
async def say_hello_text(name: str):
    the_message = f"Awesome cloud developer dff9 says Hello {name}"
    rsp = Response(content=the_message, media_type="text/plain")
    return rsp


@app.get("/students")
async def get_students():
    result = students_resource.get_students()
    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8012)

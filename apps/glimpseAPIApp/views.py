from django.shortcuts import render, HttpResponse, redirect
import bcrypt, sys, os, base64, datetime, hashlib, hmac, pytz
import boto3, csv, json
import requests
from django.db import models
from .models import User, Device, Event, Media, MediaComment
client = boto3.client('s3') #low-level functional API
resource = boto3.resource('s3') #high-level object-oriented API
v1_raw_bucket = resource.Bucket('pi-1')
v1_edited_bucket = resource.Bucket('pi-2')
v2_raw_bucket = resource.Bucket('users-raw-content')
v2_edited_bucket = resource.Bucket('users-edited-content') 

# Initializing the database 
# Only to be used once at the very beginning of launching the website to transfer all of the 
# existing files that are stored in the s3 database but not yet tracked in the sql database specific
# to the api that we are using
# Once the api is able to continually update the sql database every time an image is uploaded 
# this function will never have to be run again



def updateDatabase(request):
    thisUsersContentRaw = v2_raw_bucket.objects.filter()
    thisUsersContentEdited = v2_edited_bucket.objects.filter()
    if (User.objects.filter(id = 1)):
        print("Initial User exists")
    else:
        User.objects.create(
            # user_name = "glimpse",
            first_name = "glimpse",
            last_name = "project",
            email = "drose@glimpsewearables.com",
            phone = "5094818244",
            password = "password",
            created_at = datetime.time,
            updated_at = datetime.time
        )
    if(Device.objects.filter(id = 1)):
        print("Inital Device exists")
    else:
        Device.objects.create(
            device_number = 1,
            serial_number = "1a2b3c4d5e6f7g",
            user_id = 1
        )
    if(Event.objects.filter(id = 1)):
        print("Inital Event in database exists")
    else:
        Event.objects.create(
            name = "glimpsewearables concert",
            lat = 47.6062,
            long = 122.3321,
            address = "4637 21st Ave NE",
        )
    # This function is the most important for updating the database, checking to see if all of the images
    # that are in the s3 database are accounted for in the sql database
    for data in thisUsersContentRaw:
        if Media.objects.filter(link = data.key):
            print(data.key + "data.key already exists")
        else:
            # If else statement that helps decide whether or not this media type is a image or video
            check_image_video = data.key.lower()
            data_type = ""
            if check_image_video.endswith(".jpg") or check_image_video.endswith(".jpeg") or check_image_video.endswith(".png"):
                print("it is an image")
                data_type = "image"
            elif check_image_video.endswith(".mp4"):
                print("it is a video")
                data_type = "video"
            elif check_image_video.endswith("/"):
                data_type = "this is a folder"
            else:
                data_type = "not a jpg/jpeg or mp4"
            Media.objects.create(
                media_type = data_type,
                link = "https://s3.amazonaws.com/users-raw-content/" + data.key,
                device_id = 0,
                user_id = 0,
                event_id = 0,
                raw_or_edited = "raw"
            )
            print("adding new edited media with " + data.key + " as a the link")
    # This function is the most important for updating the database, checking to see if all of the images
    # that are in the s3 database are accounted for in the sql database
    for data in thisUsersContentEdited:
        if Media.objects.filter(link = data.key):
            print(data.key + "data.key already exists")
        else:
            # If else statement that helps decide whether or not this media type is a image or video
            # Reuse this function for adding image to database every time a new image is uploaded to the s3 database
            check_image_video = data.key.lower()
            data_type = ""
            if check_image_video.endswith(".jpg") or check_image_video.endswith(".jpeg") or check_image_video.endswith(".png"):
                print("it is an image")
                data_type = "image"
            elif check_image_video.endswith(".mp4"):
                print("it is a video")
                data_type = "video"
            elif check_image_video.endswith("/"):
                data_type = "this is a folder"
            else:
                data_type = "not a jpg/jpeg or mp4"
            Media.objects.create(
                media_type = data_type,
                link = "https://s3.amazonaws.com/users-edited-content/" + data.key,
                device_id = 0,
                user_id = 0,
                event_id = 0,
                raw_or_edited = "edited"
            )
            print("adding new edited media with " + data.key + " as a the link")
    return HttpResponse(thisUsersContentRaw)



# All of the endpoints for pushing information from the api call
# functions divider
# functions divider
# functions divider
def createUser(first_name, last_name, email, password, phone):
    User.objects.create(
        first_name = first_name,
        last_name = last_name,
        email = email,
        phone = phone,
        password = password,
        created_at = datetime.time,
        updated_at = datetime.time
    )

def createEvent(name, address, start_date, end_date, longitude, lat):
    print("creating a new event")
    now = datetime.datetime.now(pytz.timezone('US/Pacific'))
    Event.objects.create(
        name = name,
        address = address,
        start_date = start_date,
        end_date = end_date,
        long = longitude,
        lat = lat,
        created_at = now,
        updated_at = now
    )

# Converting the object based data into json data that can be parsed and returned by the api
def jsonifyMediaData(data):
    context = {}
    all_media = []
    for data_point in data:
        adding_context = {
                "link" : data_point.link,
                "user_id" : str(data_point.user_id),
                "device_id" : str(data_point.device_id),
                "event_id" : str(data_point.event_id),
                "media_type" : data_point.media_type,
                "raw_or_edited" : data_point.raw_or_edited,
                "downloaded" : data_point.downloaded,
                "ranking" : data_point.ranking,
                "created_at" : str(data_point.created_at),
                "updated_at" : str(data_point.updated_at),
                "gif_link" : data_point.gif_link
            }
        all_media.append(adding_context)
    context.update({"media" : all_media})
    return context

def jsonifyEventData(data_point):
    adding_context = {
            "name" : data_point.name,
            "address" : data_point.address,
            "start_date" : str(data_point.start_date),
            "end_date" : str(data_point.end_date),
            "long" : str(data_point.long),
            "lat" : str(data_point.lat),
            "created_at" : str(data_point.created_at),
            "updated_at" : str(data_point.updated_at)
        }
    return adding_context

def jsonifyDeviceData(data):
    context = {}
    all_events = []
    for data_point in data:
        adding_context = {
            "serial_number" : data_point.serial_number,
            "device_number" : data_point.device_number,
            "user_id" : data_point.user_id,
            "created_at" : str(data_point.created_at),
            "updated_at" : str(data_point.updated_at)
        }
        all_events.append(adding_context)
    context.update({"devices" : all_events})
    return context

def jsonifyUserData(data):
    context = {}
    all_users = []
    for data_point in data:
        adding_context = {
            "user_name" : data_point.user_name,
            "first_name" : data_point.first_name,
            "last_name" : data_point.last_name,
            "email" : data_point.email,
            "phone" : data_point.phone,
            "password" : data_point.password,
            "created_at" : str(data_point.created_at),
            "updated_at" : str(data_point.updated_at)
        }
        all_users.append(adding_context)
    context.update({"users" : all_users})
    return context


# All of the endpoints for retrieving information from the api call
# functions divider
# functions divider
# functions divider

# all the endpoint functions for retrieving media information
def index(request): # this is the standard endpoint that will not return anything
    return render(request, "portal.html")

def login(request):
    if request.method=="POST":
        device_number = request.POST['deviceNumber']
        request.session["deviceNumber"] = device_number
    return redirect("/userPage/" + device_number)

def userPage(request, device_number):
    this_device_content = Media.objects.filter(user_id = device_number)
    all_events = Event.objects.all()
    this_users_event_content = {}
    this_users_event_content["all_my_events"] = {}
    this_users_event_content["all_events"] = all_events
    for event in all_events:
        if this_device_content.filter(event_id = event.id):
            all_content = this_device_content.filter(event_id = event.id)
            this_images = this_device_content.filter(event_id = event.id, media_type = "image")
            this_videos = this_device_content.filter(event_id = event.id, media_type = "video")
            this_content = {
                "images" : this_images, 
                "videos" : this_videos
            }
            print("event " + str(event.id) + ", with content " + str(this_content))
            this_users_event_content[event.id] = this_content
    this_users_event_content["device_number"] = device_number
    # this_users_event_content["media"] = this_device_content
    return render(request, "userPage.html", this_users_event_content)

def checkLogin():
    if request.session["deviceNumber"]:
        return True
    else:
        return False

def adminLogin(request):
    if request.method=="POST":
        my_date = datetime.datetime.now(pytz.timezone('US/Pacific'))
        adminName = request.POST['adminName']
        adminPassword = request.POST['adminPassword']
    return redirect('/adminPage')

def adminPage(request):
    all_images = Media.objects.filter(media_type = "image")
    all_videos = Media.objects.filter(media_type = "video")
    context = {
        "image_number" : len(all_images), 
        "all_videos" : all_videos,
        "video_number" : len(all_videos),
        "all_users" : User.objects.all(),
        "all_events" : Event.objects.all(),
        "event_number" :len(Event.objects.all()),
        "all_devices" : Device.objects.all(),
        "device_number" : len(Device.objects.all())
    }
    return render(request, "adminPage.html", context)
def viewEventMedia(request, event_id):
    context = {}
    this_event = Event.objects.get(id = event_id)
    this_event_images = Media.objects.filter(event_id = event_id, media_type = "image")
    this_event_videos = Media.objects.filter(event_id = event_id, media_type = "video")
    context["this_event"] = this_event
    context["this_event_images"] = this_event_images
    context["this_event_videos"] = this_event_videos
    return render(request, "viewMedia.html", context)

def mediaHome(request):
    response = "here is the home page from the media application portion of the api"
    return HttpResponse(response)

def getAllImages(request): # grabs ALL images that are being stored in the raw bucket
    context = {}
    all_images = Media.objects.filter(media_type = "image")
    json_images = jsonifyMediaData(all_images)
    newContext = json.dumps(json_images)
    return HttpResponse(newContext, content_type="application/json")
    # return json(json_images)

def getAllVideos(request): # grabs ALL videos that are being stored in the raw bucket
    context = {}
    all_videos = Media.objects.filter(media_type = "video")
    json_videos = jsonifyMediaData(all_videos)
    newContext = json.dumps(json_videos)
    return HttpResponse(newContext, content_type="application/json")

def getAllUserMedia(request, userId): # grabs ALL images connected to the specific user that are being stored in the raw bucket
    context = {}
    if User.objects.filter(id = userId):
        response = "Getting all media specific to user " + userId + "..!! "
        raw_media = Media.objects.filter(user_id = userId, raw_or_edited = "raw")
        edited_media = Media.objects.filter(user_id= userId, raw_or_edited = "edited")
        json_raw_media = jsonifyMediaData(raw_media)
        json_edited_media = jsonifyMediaData(edited_media)
        context["raw_media"] = json_raw_media
        context["edited_media"] = json_edited_media
    else:
        context["error"] = "You entered a user that does not exist"
    newContext = json.dumps(context)
    return HttpResponse(newContext, content_type="application/json")

def getAllUserVideos(request, userId): # grabs ALL videos connected to the specific user that are being stored in the raw bucket
    context = {}
    if User.objects.filter(id = userId):
        response = "Getting all videos specific to a user..."
        videos_raw = Media.objects.filter(user_id = userId, media_type = "video", raw_or_edited = "raw")
        videos_edited = Media.objects.filter(user_id = userId, media_type = "video", raw_or_edited = "edited")
        json_raw_videos = jsonifyMediaData(videos_raw)
        json_edited_videos = jsonifyMediaData(videos_edited)
        context["raw_videos"] = json_raw_videos
        context["edited_videos"] = json_edited_videos
    else:
        context["error"] = "You entered a user that does not exist"
    newContext = json.dumps(context)
    return HttpResponse(newContext, content_type="application/json")

def getAllImagesUserEvent(request, userId, eventId): # grabs all images for a specific user at a specific event
    context = {}
    if Event.objects.filter(id = eventId) and Device.objects.filter(id = userId):
        response = "Getting all images for a single user at a specific event with a event id of" + eventId
        user_event_images = Media.objects.filter(event_id = eventId, user_id = userId, media_type="image")
        json_user_event_images = jsonifyMediaData(user_event_images)
        context["user_event_images"] = json_user_event_images
    else:
        context["error"] = "You entered a user or event that does not exist"
    return HttpResponse(json.dumps(context), content_type="application/json")

def getAllVideosUserEvent(request, userId, eventId): # grabs all videos for a specific user at a specific event
    context = {}
    if Event.objects.filter(id = eventId) and Device.objects.filter(id = userId):
        response = "Getting all videos for a single user at a specific event with a event id of" + eventId
        user_event_videos = Media.objects.filter(event_id = eventId, user_id = userId, media_type="video")
        json_user_event_videos = jsonifyMediaData(user_event_videos)
        context["user_event_videos"] = json_user_event_videos
    else:
        context["error"] = "You entered a user or event that does not exist"
    return HttpResponse(json.dumps(context), content_type="application/json")

# all of the endpoint functions for retrieving event information
def getAllEvents(request): # grabs ALL events from mysql database
    response = "Getting all events that have been created"
    context = {}
    all_events = Event.objects.all()
    all_images = Media.objects.filter(media_type = "image")
    all_videos = Media.objects.filter(media_type = "video")
    context["all_events"] = jsonifyEventData(all_events)
    context["all_images"] = jsonifyMediaData(all_images)
    context["all_videos"] = jsonifyMediaData(all_videos)
    newContext = json.dumps(context)
    return HttpResponse(newContext, content_type="application/json")

def getSpecificEvent(request, eventId): # grabs a specific event from the mySQL database
    context = {}
    newContext = {}
    if Event.objects.filter(id = eventId):
        response = "Getting a single specific event with a event id of"
        this_event = Event.objects.get(id = eventId)
        this_event_content = Media.objects.filter(event_id = eventId)
        context["this_event"] = jsonifyEventData(this_event)
        context["this_event_content"] = jsonifyMediaData(this_event_content)
        newContext = json.dumps(context)
    else:
        newContext["error"] = "You entered a event that does not exist"
    return HttpResponse(newContext, content_type="application/json")

# all of the endpoint functions for retrieving device information
def getAllDevices(request): # grabs a specific user from the mySQL database
    all_devices = Device.objects.all()
    context = jsonifyDeviceData(all_devices)
    newContext = json.dumps(context)
    return HttpResponse(newContext, content_type="application/json")

def getSpecificDevice(request, device_id): # grabs all users from the mySQL database
    context = {}
    if Device.objects.filter(id = device_id):
        this_device = User.objects.filter(id=device_id)
        context = jsonifyUserData(this_device)
    else:
        context["error"] = "You entered a device that does not exist"
    newContext = json.dumps(context)
    return HttpResponse(newContext, content_type="application/json")

# all of the endpoint functions for retrieving user information
def getAllUsers(request): # grabs a specific user from the mySQL database
    all_users = User.objects.all()
    context = jsonifyUserData(all_users)
    newContext = json.dumps(context)
    return HttpResponse(newContext, content_type="application/json")

def getSpecificUser(request, user_id): # grabs all users from the mySQL database
    context = {}
    if User.objects.filter(id = user_id):
        this_user = User.objects.filter(id=user_id)
        context = jsonifyUserData(this_user)
    else:
        context["error"] = "You entered a user that does not exist"
    newContext = json.dumps(context)
    return HttpResponse(newContext, content_type="application/json")

def getSpecificUserByEmail(request, user_email):
    context = {}
    if User.objects.filter(email = user_email):
        this_user = User.objects.filter(email = user_email)
        context = jsonifyUserData(this_user)
    else:
        context["error"] = "You entered a user that does not exist"
    newContext = json.dumps(context)
    return HttpResponse(newContext, content_type="application/json")
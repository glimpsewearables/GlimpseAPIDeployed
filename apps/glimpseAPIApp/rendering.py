from django.shortcuts import render, HttpResponse, redirect, HttpResponseRedirect
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


# This is the page with all of the functions for viewing and rendering pages 
def index(request): # this is the standard endpoint that will not return anything
    return render(request, "portal.html")

def login(request):
    if request.method=="POST":
        device_number = request.POST['deviceNumber']
        request.session["deviceNumber"] = device_number
        request.session["userType"] = "user"
    return redirect("/userPage/" + device_number)

def userPage(request, device_number):
    if request.session["userType"] != "user" and request.session["userType"] != "admin" :
        return redirect("/")
    else:
        this_device_content = Media.objects.filter(user_id = device_number, media_type = "video").order_by('created_at')
        all_events = Event.objects.all().order_by('created_at').reverse()
        most_recent = this_device_content.order_by('-id')[:9]
        this_users_event_content = {}
        this_users_event_content["all_events"] = all_events
        this_users_event_content["my_events"] = []
        this_users_event_content["device_number"] = device_number
        this_users_event_content["most_recent"] = most_recent
        this_users_event_content["total_vids"] = len(this_device_content)
        this_users_event_content["last_video"] = this_device_content[:1]
        this_users_event_content["userType"] = request.session["userType"]
        for event in all_events:
            if this_device_content.filter(event_id = event.id):
                this_users_event_content["event" + str(event.id)] = {"videos": this_device_content.filter(event_id = event.id)}
                this_users_event_content["my_events"].append(event.id)
        return render(request, "userPage.html", this_users_event_content)

def checkLogin():
    if request.session["deviceNumber"]:
        return True
    else:
        return False

def adminLogin(request):
    if request.method=="POST":
        adminName = request.POST['adminName']
        adminPassword = request.POST['adminPassword']
        if adminName != "Dylan Rose" or adminPassword != "isourboss":
            return redirect("/")
        else:
            request.session["userType"] = "admin"
            return redirect('/adminPage')

def adminPage(request):
    if request.session["userType"] != "admin":
        return redirect("/")
    else:
        all_images = Media.objects.filter(media_type = "image")
        all_videos = Media.objects.filter(media_type = "video").order_by('created_at').reverse()
        currentEvent = Event.objects.get(id = request.session["currentEventId"])
        last_video = all_videos.last()
        context = {
            "userType" : request.session["userType"],
            "image_number" : len(all_images), 
            "all_videos" : all_videos,
            "video_number" : len(all_videos),
            "all_users" : User.objects.all(),
            "all_events" : Event.objects.all(),
            "event_number" :len(Event.objects.all()),
            "currentEvent" : currentEvent,
            "all_devices" : Device.objects.all(),
            "device_number" : len(Device.objects.all()),
            "last_video" : last_video
        }
        return render(request, "adminPage.html", context)

def viewEventMedia(request, event_id):
    if request.session["userType"] != "admin":
        return redirect("/")
    else:
        context = {}
        this_event = Event.objects.get(id = event_id)
        this_event_images = Media.objects.filter(event_id = event_id, media_type = "image")
        this_event_videos = Media.objects.filter(event_id = event_id, media_type = "video")
        context["this_event"] = this_event
        context["userType"] = request.session["userType"]
        context["this_event_images"] = this_event_images
        context["this_event_videos"] = this_event_videos
        return render(request, "viewMedia.html", context)

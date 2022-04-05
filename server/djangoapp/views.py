from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
# from .models import related models
from .models import CarModel
# from .restapis import related methods
from .restapis import get_dealers_from_cf, get_dealer_reviews_from_cf, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.

# An `about` view to render a static about page
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)


# A `contact` view to return a static contact page
def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/contact.html', context)
    

# A `login_request` view to handle sign in request
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'djangoapp/index.html', context)
    else:
        return render(request, 'djangoapp/index.html', context)



# A `logout_request` view to handle sign out request
def logout_request(request):
    # Get the user object based on session id in request
    print("Log out the user `{}`".format(request.user.username))
    # Logout user in the request
    logout(request)
    return redirect('djangoapp:index')

# A `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    # If it is a GET request, just render the registration page
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    # If it is a POST request
    elif request.method == 'POST':
        # Get user information from request.POST
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            # Check if user already exists
            User.objects.get(username=username)
            user_exist = True
        except:
            # If not, simply log this is a new user
            logger.debug("{} is new user".format(username))
        # If it is a new user
        if not user_exist:
            # Create user in auth_user table
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            # Login the user and redirect to About page
            login(request, user)
            return redirect("djangoapp:about")
        else:
            return render(request, 'djangoapp/index.html', context)

# A `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    context = {}
    if request.method == "GET":
        url = "https://22bc8b95.us-south.apigw.appdomain.cloud/api/dealership/get-dealerships"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)
        context['dealerships'] = dealerships
        # Concat all dealer's short name
        #dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        # Return a list of dealer short name
        # context['dealership_list'] = dealerships
        #context = {'dealer_names': dealer_names}
        return render(request, 'djangoapp/index.html', context)
        # return HttpResponse(dealer_names)


# A `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealerId):
    context = {}
    if request.method == "GET":
        url = "https://22bc8b95.us-south.apigw.appdomain.cloud/api/review"
        # Get dealership reviews from the URL
        reviews = get_dealer_reviews_from_cf(url, dealerId)
        context['reviews'] = reviews
        context['dealerId'] = dealerId
        context['dealer'] = get_dealer_detail_infos(dealerId)
        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
def add_review(request, dealerId):
    context = dict()

    if request.method == 'GET':
        context['dealerId'] = dealerId
        context['cars'] = CarModel.objects.filter(dealerId=dealerId)
        context['dealer'] = get_dealer_detail_infos(dealerId)
        return render(request, 'djangoapp/add_review.html', context)

    if request.method == "POST":
        user = request.user
        if user.is_authenticated:
            review_content = request.POST['review']
            car_id = int(request.POST['car'])
            car = get_object_or_404(CarModel, pk=car_id)
            purchase_date = request.POST['purchase_date']
            
            review = dict()
            #review["id"] = uuid.uuid4().hex
            if 'purchase' in request.POST:
                review["purchase"] = True
            else:
                review["purchase"] = False
            review["dealership"] = dealerId 
            review["review"] = review_content 	
            review["name"] = user.get_full_name()  
            review['car_make'] = car.brand.name 
            review['car_model'] = car.name 
            review['car_year'] = car.year.strftime("%Y")
            review['purchase_date'] = datetime.strptime(purchase_date, '%Y-%m-%d').strftime('%m/%d/%Y')
            
            json_payload = dict()
            json_payload["review"] = review
            url = 'https://22bc8b95.us-south.apigw.appdomain.cloud/post_review'
            
            post_request(url, json_payload, dealerId=dealerId)
            return redirect("djangoapp:dealer_details", dealerId=dealerId)
    else:
            return render(request, 'djangoapp/index.html', context)

def get_dealer_detail_infos(dealerId):
    url = "https://22bc8b95.us-south.apigw.appdomain.cloud/api/dealership/get-dealerships"
    dealerships = get_dealers_from_cf(url)
    return next(filter(lambda x: x.id == dealerId, dealerships))

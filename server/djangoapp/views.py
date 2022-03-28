from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
# from .models import related models
from .models import CarModel
# from .restapis import related methods
from .restapis import get_dealers_from_cf, get_dealer_by_id_from_cf, get_dealer_reviews_from_cf, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
# def about(request):
# ...
def about(request):
    # If the request method is GET
    if request.method == 'GET':
        return render(request, 'djangoapp/about.html')


# Create a `contact` view to return a static contact page
#def contact(request):
def contact(request):
    # If the request method is GET
    if request.method == 'GET':
        return render(request, 'djangoapp/contact.html')



# Create a `login_request` view to handle sign in request
# def login_request(request):
# ...
def login_request(request):
    context = {}
    # Handles POST request
    if request.method == "POST":
        # Get username and password from request.POST dictionary
        username = request.POST['username']
        password = request.POST['psw']
        # Try to check if provide credential can be authenticated
        user = authenticate(username=username, password=password)
        if user is not None:
            # If user is valid, call login method to login current user
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            # If not, return to login page again
            return render(request, 'djangoapp/login.html', context)
    else:
        return render(request, 'djangoapp/login.html', context)

# Create a `logout_request` view to handle sign out request
# def logout_request(request):
# ...
def logout_request(request):
    # Get the user object based on session id in request
    print("Log out the user `{}`".format(request.user.username))
    # Logout user in the request
    logout(request)
    # Redirect user back to course list view
    return redirect('djangoapp:index')


# Create a `registration_request` view to handle sign up request
# def registration_request(request):
# ...
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'djangoapp/registration.html', context)


# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        context = {}
        url = "https://22bc8b95.us-south.apigw.appdomain.cloud/api/dealership/get-dealerships"
        dealerships = get_dealers_from_cf(url)
        context['dealership_list'] = dealerships
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
# ...
def get_dealer_details(request, dealer_id):
    if request.method == "GET":
        context = {}

        dealer_url = "https://22bc8b95.us-south.apigw.appdomain.cloud/api/review"
        reviews = get_dealer_reviews_from_cf(dealer_url, dealer_id)
        context["review_list"] = reviews

        dealer_url = "https://22bc8b95.us-south.apigw.appdomain.cloud/api/dealership/get-dealerships"
        dealer = get_dealer_by_id_from_cf(dealer_url, id=dealer_id)
        context["dealer"] = dealer
     
        return render(request, 'djangoapp/dealer_details.html', context)


##
def get_dealer_reviews_from_cf(url, dealerId):
    results = []

    json_result = get_request(url, dealerId=dealerId)

    if json_result:
        reviews = json_result["body"]["data"]["docs"]

        for dealer_review in reviews:  
            review_obj = DealerReview(dealership=dealer_review["dealership"],
                                      name=dealer_review["name"], 
                                      purchase=dealer_review["purchase"], 
                                      review=dealer_review["review"])
 	
            if 'purchase_date' in dealer_review:
                review_obj.purchase_date = dealer_review['purchase_date']

            if 'car_make' in dealer_review:
                review_obj.car_make = dealer_review['car_make']

            if 'car_model' in dealer_review:
                review_obj.car_model = dealer_review['car_model']

            if 'car_year' in dealer_review:
                review_obj.car_year = dealer_review['car_year']

            if 'id' in dealer_review:
                review_obj.id = dealer_review['id']

            sentiment = analyze_review_sentiments(review_obj.review)
            print(sentiment)
            review_obj.sentiment = sentiment
            results.append(review_obj)

    return results

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# ...
# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    context = {}
    dealer_url = "https://22bc8b95.us-south.apigw.appdomain.cloud/api/dealership/get-dealerships"
    dealer = get_dealer_by_id_from_cf(dealer_url, id=dealer_id)
    context["dealer"] = dealer

    if request.method == 'GET':
        # Get cars for the dealer
        cars = CarModel.objects.filter(dealer_id=dealer_id)
        context["cars"] = cars        
        return render(request, 'djangoapp/add_review.html', context)

    elif request.method == 'POST':
        if request.user.is_authenticated:
            username = request.user.username
            print(request.POST)
            payload = dict()
            car_id = request.POST["car"]
            car = CarModel.objects.get(pk=car_id)
            payload["time"] = datetime.utcnow().isoformat()
            payload["name"] = username
            payload["dealership"] = dealer_id
            payload["id"] = dealer_id
            payload["review"] = request.POST["content"]
            payload["purchase"] = False
            if "purchasecheck" in request.POST:
                if request.POST["purchasecheck"] == 'on':
                    payload["purchase"] = True
            payload["purchase_date"] = request.POST["purchasedate"]
            payload["car_make"] = car.make.name
            payload["car_model"] = car.name
            payload["car_year"] = int(car.year.strftime("%Y"))

            new_payload = {}
            new_payload["review"] = payload
            review_post_url = "https://22bc8b95.us-south.apigw.appdomain.cloud/post_review/post_review"
            post_request(review_post_url, new_payload, id=dealer_id)
        return redirect("djangoapp:dealer_details", dealer_id=dealer_id)



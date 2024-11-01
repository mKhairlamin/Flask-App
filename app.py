import csv
from flask import Flask, render_template, request, send_from_directory
import math
import os

app = Flask(__name__)

# Load the car data without pandas
def load_car_data(file_path):
    cars = []
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert columns to appropriate types
            row['Price (RM)'] = float(row['Price (RM)']) if row['Price (RM)'] else 0.0
            row['Fuel_Consumption'] = float(row['Fuel_Consumption']) if row['Fuel_Consumption'] else 0.0
            row['Seats'] = int(row['Seats']) if row['Seats'] else 0
            row['Boot_Capacity'] = int(row['Boot_Capacity']) if row['Boot_Capacity'] else 0
            row['Total Displacement (CC)'] = int(row['Total Displacement (CC)']) if row['Total Displacement (CC)'] else 0
            row['Fuel_Tank'] = float(row['Fuel_Tank']) if row['Fuel_Tank'] else 0.0
            row['ID'] = int(row['ID']) if row['ID'] else 0
            cars.append(row)
    return cars

# Load the cars data
cars_data = load_car_data('Malaysian_Dataset_final.csv')

# Function to calculate cosine similarity
def cosine_similarity(vec_a, vec_b):
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a ** 2 for a in vec_a))
    norm_b = math.sqrt(sum(b ** 2 for b in vec_b))
    
    if norm_a == 0 or norm_b == 0:
        return 0
    return dot_product / (norm_a * norm_b)

# Function to get recommendations by cosine similarity
def get_recommendations_by_cosine_similarity(user_preferences):
    recommendations = []
    for car in cars_data:
        car_features = [
            car['Price (RM)'],
            car['Fuel_Consumption'],
            car['Seats'],
            car['Boot_Capacity'],
            car['Total Displacement (CC)'],
            car['Fuel_Tank']
        ]
        similarity_score = cosine_similarity(user_preferences[0], car_features)
        if similarity_score > 0:
            car_copy = car.copy()
            car_copy['Similarity'] = round(similarity_score * 100, 2)
            recommendations.append(car_copy)

    # Sort by similarity
    recommendations_sorted = sorted(recommendations, key=lambda x: x['Similarity'], reverse=True)
    return recommendations_sorted

# Functions for monthly payment and desired amount filtering
def get_recommendations_by_monthly_payment(user_salary, num_years, deposit_percentage, interest_percentage):
    monthly_payment = user_salary / 3
    recommendations = []
    for car in cars_data:
        interest_payment = (interest_percentage / 100) * car['Price (RM)'] * num_years
        down_payment = deposit_percentage * car['Price (RM)']
        total_payment = (car['Price (RM)'] + interest_payment) - down_payment
        if total_payment <= monthly_payment * (num_years * 12):
            recommendations.append(car)
    return sorted(recommendations, key=lambda x: x['Price (RM)'])

def get_recommendations_by_desired_amount(desired_amount, num_years, deposit_percentage, interest_percentage):
    recommendations = []
    for car in cars_data:
        interest_payment = (interest_percentage / 100) * car['Price (RM)'] * num_years
        down_payment = deposit_percentage * car['Price (RM)']
        total_payment = (car['Price (RM)'] + interest_payment) - down_payment
        if total_payment <= desired_amount * (num_years * 12):
            recommendations.append(car)
    return sorted(recommendations, key=lambda x: x['Price (RM)'])

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route for the findCar page
@app.route('/findCar')
def find_car():
    return render_template('findCar.html')

# Route for handling form submission
@app.route('/recommendations', methods=['POST'])
def recommendations():
    user_salary = float(request.form['salary'])
    desired_amount = float(request.form['amount'])
    num_years = int(request.form['years'])
    deposit_percentage = float(request.form['deposit'])
    interest_percentage = float(request.form['interest'])
    cc = float(request.form['cc'])
    luggage = int(request.form['Boot_Capacity'])
    fuel_tank_capacity = float(request.form['Fuel_Tank'])
    fuel_consumption = float(request.form['Fuel_Consump'])
    car_seats = int(request.form['CarSeater'])

    user_payment = (user_salary / 3) * (num_years * 12)

    recommendations_monthly_payment = get_recommendations_by_monthly_payment(user_salary, num_years, deposit_percentage, interest_percentage)
    recommendations_sortedbyprice = sorted(recommendations_monthly_payment, key=lambda x: x['Price (RM)'])

    recommendations_desired_amount = get_recommendations_by_desired_amount(desired_amount, num_years, deposit_percentage, interest_percentage)
    recommendations_sortedbydesired = sorted(recommendations_desired_amount, key=lambda x: x['Price (RM)'])
    
    user_preferences = [[user_payment, fuel_consumption, car_seats, luggage, cc, fuel_tank_capacity]]
    recommendations_by_cosine_similarity = get_recommendations_by_cosine_similarity(user_preferences)

    user_desired = [[desired_amount * (num_years * 12), fuel_consumption, car_seats, luggage, cc, fuel_tank_capacity]]
    recommendations_by_desired = get_recommendations_by_cosine_similarity(user_desired)
    
    return render_template('recommendations.html', 
                           monthly_payment=user_salary / 3,
                           total_months=num_years * 12,
                           desired_payment=desired_amount,
                           interest_payment=interest_percentage,
                           down_payment=deposit_percentage,
                           recommendations_monthly_payment=recommendations_sortedbyprice,
                           recommendations_desired_amount=recommendations_sortedbydesired,
                           recommendations_cosine_similarity=recommendations_by_cosine_similarity,
                           recommendations_desired=recommendations_by_desired)

# Route to serve images from the assets folder
@app.route('/assets/<path:filename>')
def send_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'assets'), filename)

# Route for the car details page
@app.route('/car/<int:car_id>')
def car_details(car_id):
    car = next((car for car in cars_data if car['ID'] == car_id), None)
    return render_template('car_details.html', car=car)

@app.route('/cars/<brand>')
def brand_cars(brand):
    brand = brand.capitalize()
    filtered_cars = [car for car in cars_data if car['Brand'] == brand]
    filtered_cars = sorted(filtered_cars, key=lambda x: x['Price (RM)'])
    return render_template('brand_cars.html', brand=brand, cars=filtered_cars)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, render_template, request, send_file, redirect, url_for, session
import pandas as pd
import os
from price_optimizer_consolidated import run_price_optimizer
from mmm_optimizer_consolidated import run_mmm_optimizer
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def format_currency(value):
    return f"{value:,.2f}"

####################home page routes####################
#landing page
@app.route('/')
def root():
    # Redirect to the login page when the app loads
    return redirect(url_for('login'))


#render index page when someone logs in using post method and render the login page when someone lands on the login page using get method
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Skip authentication and redirect to the index page
        return redirect(url_for('index'))
    return render_template('login.html')

#render index page
@app.route('/index')
def index():
    return render_template(
        'index.html',
    )

#render login page when someone logs out
@app.route('/logout')
def logout():
    # Redirect to the login page on logout
    return redirect(url_for('login'))

###############price optimizer routes#####################

#save the inputs to price optimizer page in session and render the price optimizer page when refreshed
@app.route('/priceoptimizer', methods=['GET'])
def priceoptimizer():
    # Load saved inputs from session if they exist
    saved_inputs = session.get('user_inputs', {})
    return render_template('priceoptimizer.html', saved_inputs=saved_inputs, last_uploaded_file=session.get('last_uploaded_file'))

#save the inputs to price optimizer page in session and render the price optimizer page when refreshed
@app.route('/marketedge', methods=['GET'])
def marketedge():
    # Load saved inputs from session if they exist
    saved_inputs = session.get('user_inputs', {})
    return render_template('marketedge.html', saved_inputs=saved_inputs, last_uploaded_file=session.get('last_uploaded_file'))


#####price optimizer route#####
# Process the uploaded file and user inputs when someone submits the form for price optimizer
@app.route('/processpriceoptimizer', methods=['POST'])
def process():
    error_message = None
    #read the file from the form
    uploaded_file = request.files['file']
    # Validate file upload
    if uploaded_file.filename == '':
        error_message = "Please upload a CSV file."
    elif not uploaded_file.filename.lower().endswith('.csv'):
        error_message = "Only CSV files are supported."

    # Clean up any non numeric characters from numeric fields(excpet .)
    def clean_percent_seperators(val):
        if val is None:
            return ''
        return re.sub(r'[^0-9.]+', '', str(val)).strip()
    


    user_inputs_priceoptimization = {
        'optimization': request.form.get('optimization'),
        'quantity_min': clean_percent_seperators(request.form.get('quantity_min', '')),
        'quantity_max': clean_percent_seperators(request.form.get('quantity_max', '')),
        'discount_min': clean_percent_seperators(request.form.get('discount_min', '')),
        'discount_max': clean_percent_seperators(request.form.get('discount_max', '')),
        'sales_min': clean_percent_seperators(request.form.get('sales_min', '')),
        'sales_max': clean_percent_seperators(request.form.get('sales_max', '')),
        'profit_min': clean_percent_seperators(request.form.get('profit_min', '')),
        'profit_max': clean_percent_seperators(request.form.get('profit_max', '')),
        'profitability_min': clean_percent_seperators(request.form.get('profitability_min', '')),
        'profitability_max': clean_percent_seperators(request.form.get('profitability_max', '')),
    }

    # Save user inputs to session(this will ensure that the inputs are there in the form even when we have run the optimizer)
    session['user_inputs_priceoptimization'] = user_inputs_priceoptimization

    # Validate numeric fields (allow empty, but if not empty, must be a number)
    numeric_fields = [
        'quantity_min', 'quantity_max', 'discount_min', 'discount_max',
        'sales_min', 'sales_max', 'profit_min', 'profit_max',
        'profitability_min', 'profitability_max'
    ]
    for field in numeric_fields:
        val = user_inputs_priceoptimization[field]
        if val and not re.match(r'^-?\d+(\.\d+)?$', val):
            error_message = f"'{field.replace('_', ' ').title()}' must be a number."
            break
#render the price optimization page with error message if validation fails
    if error_message:
        return render_template(
            'priceoptimizer.html',
            saved_inputs=user_inputs_priceoptimization,
            last_uploaded_file=session.get('last_uploaded_file'),
            error_message=error_message
        )

    # Save uploaded file with original filename (no timestamp)
    filename = uploaded_file.filename
    upload_file_path = os.path.join(UPLOAD_FOLDER, filename)
    uploaded_file.save(upload_file_path)
    session['last_uploaded_file'] = filename

    # Prepare inputs for optimizer
    price_optimizer_inputs = {
        'Sales Maximization': int(user_inputs_priceoptimization['optimization'] == 'Sales Maximization'),
        'Profit Maximization': int(user_inputs_priceoptimization['optimization'] == 'Profit Maximization'),
        'Profitability Maximization': int(user_inputs_priceoptimization['optimization'] == 'Profitability Maximization'),
        'Quantity Constraint Min': user_inputs_priceoptimization['quantity_min'],
        'Quantity Constraint Max': user_inputs_priceoptimization['quantity_max'],
        'Discount % Constraint Min': user_inputs_priceoptimization['discount_min'],
        'Discount % Constraint Max': user_inputs_priceoptimization['discount_max'],
        'Sales Constraint Min': user_inputs_priceoptimization['sales_min'],
        'Sales Constraint Max': user_inputs_priceoptimization['sales_max'],
        'Profit Constraint Min': user_inputs_priceoptimization['profit_min'],
        'Profit Constraint Max': user_inputs_priceoptimization['profit_max'],
        'Profitability Constraint Min': user_inputs_priceoptimization['profitability_min'],
        'Profitability Constraint Max': user_inputs_priceoptimization['profitability_max'],
    }
    input_file_path_price_optimizer = os.path.join(UPLOAD_FOLDER, 'price_optimizer_user_inputs.csv')
    pd.DataFrame([price_optimizer_inputs]).to_csv(input_file_path_price_optimizer, index=False)

    # Run price optimizer
    try:
        final_long_df_price, total_gmv, total_gp, avg_gp_per, total_base_gmv, total_base_gp, avg_base_gp_per = run_price_optimizer(upload_file_path, input_file_path_price_optimizer)
    except Exception as e:
        error_message = f"There was an error processing your file or inputs: {str(e)}"
        return render_template(
            'priceoptimizer.html',
            saved_inputs=user_inputs_priceoptimization,
            last_uploaded_file=session.get('last_uploaded_file'),
            error_message=error_message
        )

    # Save results with a fixed filename (overwrite each time)
    results_file_path = os.path.join(UPLOAD_FOLDER, 'price_optimizer_results.csv')
    final_long_df_price.to_csv(results_file_path, index=False)
    session['last_results_file'] = 'price_optimizer_results.csv'

    return render_template(
        'priceoptimizer.html',
        table=final_long_df_price.to_html(classes='data', index=False),
        titles=final_long_df_price.columns.values,
        total_gmv=total_gmv,
        total_gp=total_gp,
        avg_gp_per=avg_gp_per,
        total_base_gmv=total_base_gmv,
        total_base_gp=total_base_gp,
        avg_base_gp_per=avg_base_gp_per,
        saved_inputs=user_inputs_priceoptimization,
        last_uploaded_file=session.get('last_uploaded_file'),
        error_message=None
    )



################ Market edge routes ################
# Process the uploaded file and user inputs when someone submits the form for price optimizer
@app.route('/processmarketedge', methods=['POST'])
def processmarketedge():
    error_message = None
    #read the file from the form
    uploaded_file = request.files['file']
    # Validate file upload
    if uploaded_file.filename == '':
        error_message = "Please upload a CSV file."
    elif not uploaded_file.filename.lower().endswith('.csv'):
        error_message = "Only CSV files are supported."

    # Clean up any non numeric characters from numeric fields(excpet .)
    def clean_percent_seperators(val):
        if val is None:
            return ''
        return re.sub(r'[^0-9.]+', '', str(val)).strip()


    user_inputs_mmm = {
        'optimization': request.form.get('optimization'),
        'sales_min': clean_percent_seperators(request.form.get('sales_min', '')),
        'sales_max': clean_percent_seperators(request.form.get('sales_max', '')),
        'spend_min': clean_percent_seperators(request.form.get('spend_min', '')),
        'spend_max': clean_percent_seperators(request.form.get('spend_max', '')),
        'roi_min': clean_percent_seperators(request.form.get('roi_min', '')),
        'roi_max': clean_percent_seperators(request.form.get('roi_max', '')),
    }

    # Save user inputs to session(this will ensure that the inputs are there in the form even when we have run the optimizer)
    session['user_inputs_mmm'] = user_inputs_mmm

    # Validate numeric fields (allow empty, but if not empty, must be a number)
    numeric_fields = ['sales_min', 'sales_max', 'spend_min', 'spend_max', 'roi_min', 'roi_max' ]


    for field in numeric_fields:
        val = user_inputs_mmm[field]
        if val and not re.match(r'^-?\d+(\.\d+)?$', val):
            error_message = f"'{field.replace('_', ' ').title()}' must be a number."
            break
#render the price optimization page with error message if validation fails
    if error_message:
        return render_template(
            'marketedge.html',
            saved_inputs=user_inputs_mmm,
            last_uploaded_file=session.get('last_uploaded_file'),
            error_message=error_message
        )

    # Save uploaded file with original filename (no timestamp)
    filename = uploaded_file.filename
    upload_file_path = os.path.join(UPLOAD_FOLDER, filename)
    uploaded_file.save(upload_file_path)
    session['last_uploaded_file'] = filename

    # Prepare inputs for optimizer
    mmm_optimizer_inputs = {
        'Sales Maximization': int(user_inputs_mmm['optimization'] == 'Sales Maximization'),
        'Spend Minimization': int(user_inputs_mmm['optimization'] == 'Spend Minimization'),
        'ROI Maximization': int(user_inputs_mmm['optimization'] == 'ROI Maximization'),
        'Sales Constraint Min': user_inputs_mmm['sales_min'],
        'Sales Constraint Max': user_inputs_mmm['sales_max'],
        'Spend Constraint Min': user_inputs_mmm['spend_min'],
        'Spend Constraint Max': user_inputs_mmm['spend_max'],
        'ROI % Constraint Min': user_inputs_mmm['roi_min'],
        'ROI % Constraint Max': user_inputs_mmm['roi_max']
    }
    input_file_path = os.path.join(UPLOAD_FOLDER, 'mmm_user_inputs.csv')
    pd.DataFrame([mmm_optimizer_inputs]).to_csv(input_file_path, index=False)

    # Run mmm optimizer
    try:
        final_long_df_mmm, total_optimized_sales, total_optimized_spend, total_opimized_roi, total_base_sales,total_base_spend, total_base_roi = run_mmm_optimizer(upload_file_path, input_file_path)
    except Exception as e:
        error_message = f"There was an error processing your file or inputs: {str(e)}"
        return render_template(
            'marketedge.html',
            saved_inputs=user_inputs_mmm,
            last_uploaded_file=session.get('last_uploaded_file'),
            error_message=error_message
        )

    # Save results with a fixed filename (overwrite each time)
    results_file_path = os.path.join(UPLOAD_FOLDER, 'mmm_results.csv')
    final_long_df_mmm.to_csv(results_file_path, index=False)
    session['last_results_file'] = 'mmm_results.csv'

    return render_template(
        'marketedge.html',
        table=final_long_df_mmm.to_html(classes='data', index=False),
        titles=final_long_df_mmm.columns.values,
        total_optimized_sales=total_optimized_sales,
        total_optimized_spend=total_optimized_spend,
        total_opimized_roi = total_opimized_roi,
        total_base_sales=total_base_sales,
        total_base_spend=total_base_spend,
        total_base_roi=total_base_roi,
        saved_inputs=mmm_optimizer_inputs,
        last_uploaded_file=session.get('last_uploaded_file'),
        error_message=None
    )
    # Redirect to the marketedge page after successful processing
    return redirect(url_for('marketedge'))

@app.route('/download', methods=['POST'])
def download():
    results_file = session.get('last_results_file', 'results.csv')
    results_file_path = os.path.join(UPLOAD_FOLDER, results_file)
    return send_file(results_file_path, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port,debug=True)
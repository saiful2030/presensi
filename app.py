from flask import Flask, render_template, request, redirect, url_for, session, make_response
from mysql import connector
from fpdf import FPDF
import pandas as pd
import io
from functools import wraps

app = Flask(__name__)

app.secret_key = 'PerpetuumArc'

db = connector.connect(
    host='202.10.36.201',
    user='face_dataku',
    passwd='xctkpXKs8s8eahaD',
    database='dataku2'
)
if db.is_connected():
    print('open connection successful')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
        return redirect('/presensi/')  # Jika sudah login, redirect langsung ke halaman presensi
    message = ''
    if request.method == 'POST':
        try:
            nik = request.form['nik']

            cursor = db.cursor()
            cursor.execute(
                'SELECT namaguru FROM datapokokguru WHERE nik = %s',
                (nik,)
            )
            user = cursor.fetchone()

            if user:
                session['loggedin'] = True
                session['nik'] = nik
                session['namaguru'] = user[0]
                return redirect('/presensi/')
            else:
                message = 'Silakan masukkan NIK/kata sandi yang benar!'
        except KeyError:
            message = 'Data tidak lengkap, silakan coba lagi.'
    return render_template('login.html', message=message)

@app.route('/presensi/')
@login_required
def presensi():
    cursor = db.cursor()
    cursor.execute('SELECT * FROM presensi')
    result = cursor.fetchall()
    cursor.close()
    return render_template('index.html', hasil=result)


@app.route('/hapus/<int:id>', methods=['GET'])
def hapus(id):
    cursor = db.cursor()
    cursor.execute('DELETE FROM presensi WHERE id = %s', (id,))
    db.commit()
    cursor.close()
    return redirect(url_for('home'))


@app.route('/export/csv')
def export_csv():
    cursor = db.cursor()
    cursor.execute("""
        SELECT nisn, nama, waktu
        FROM presensi
    """)
    transaksi = cursor.fetchall()
    cursor.close()

    df = pd.DataFrame(transaksi, columns=['NISN', 'Nama', 'Waktu'])

    response = make_response(df.to_csv(index=False))
    response.headers['Content-Disposition'] = 'attachment; filename=Presensi.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


@app.route('/export/excel')
def export_excel():
    cursor = db.cursor()
    cursor.execute("""
        SELECT nisn, nama, waktu
        FROM presensi
    """)
    transaksi = cursor.fetchall()
    cursor.close()

    df = pd.DataFrame(transaksi, columns=['NISN', 'Nama', 'Waktu'])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Transaksi')

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=Presensi.xlsx'
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response


@app.route('/export/pdf')
def export_pdf():
    cursor = db.cursor()
    cursor.execute("""
        SELECT nisn, nama, waktu
        FROM presensi
    """)
    transaksi = cursor.fetchall()
    cursor.close()


    pdf = FPDF('L', 'mm', 'A4') 
    pdf.add_page()
    pdf.set_font("Arial", size=12)


    pdf.cell(280, 10, txt="Presensi", ln=True, align='C')  
    pdf.ln(10)


    pdf.cell(70, 10, 'NISN', 1)
    pdf.cell(140, 10, 'Nama', 1)
    pdf.cell(70, 10, 'Waktu', 1)
    pdf.ln()


    for t in transaksi:
        pdf.cell(70, 10, str(t[0]), 1)
        pdf.cell(140, 10, str(t[1]), 1)
        pdf.cell(70, 10, str(t[2]), 1)
        pdf.ln()


    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers['Content-Disposition'] = 'attachment; filename=Presensi.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response


@app.route("/logout/")
def logout():
    session.clear()
    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True)

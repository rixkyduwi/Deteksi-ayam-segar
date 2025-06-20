from . import app,db,History,Rekomendasi,User,bcrypt,login_role_required, DataToko
from flask import render_template, request, jsonify, redirect, url_for,session,g,abort
from io import BytesIO
import os,textwrap, locale, json, uuid, time,re
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlalchemy import extract
from datetime import datetime
from sqlalchemy.orm import aliased

#halaman homepage
@app.route('/')
def index():
    return render_template('index.html')
#halaman tips
@app.route('/tips')
def userberita():
    # tips = Berita.query.all()
    return render_template('tips.html')
#halaman dashboard user
@app.route('/user/dashboard')
@login_role_required('user')
def dashboarduser():
    #data_toko = DataToko.query.filter_by(user_id=session['id']).all()
    #print(data_toko)
    # Cek jika data toko kosong
    # if not data_toko:
    #     return redirect(url_for("profile"))
    # Check if all required fields are filled
    if not all([session.get('username'),session.get('full_name'),session.get('email')]):
        return redirect(url_for("profile"))
    else:
        #return render_template('user/dashboard.html',data = data_toko)
        return render_template('user/dashboard.html')
#halaman crud data toko
@app.route('/user/data_toko', methods=['POST'])
@login_role_required('user')
def create_data_toko():
    data = request.get_json()
    
    # Debugging purpose
    print(data)
    
    nama_toko = data.get('nama_toko')
    usia_toko = data.get('usia_toko')
    jenis_toko = data.get('jenis_toko')

    try:
        # Validasi input
        if not nama_toko or not usia_toko or jenis_toko not in ['L', 'P']:
            return jsonify({"msg": "Invalid data"}), 400
        cek_nama_toko = DataToko.query.filter_by(user_id=session["id"]).all()
        print(cek_nama_toko)
        for toko in cek_nama_toko :
            print(toko.nama_toko)
            print(nama_toko)
            if toko.nama_toko == nama_toko:
                return jsonify({"msg":"maaf nama toko tidak boleh sama "})
        # Membuat instance DataToko
        data_toko = DataToko(
            user_id=session['id'],
            nama_toko=nama_toko,
            usia_toko=usia_toko,
            jenis_toko=jenis_toko
        )
        db.session.add(data_toko)
        db.session.commit()

        return jsonify({"msg": "Data Toko berhasil ditambahkan"}), 201

    except Exception as e:
        db.session.rollback()
        # Log the actual error message somewhere secure
        print(f"Error: {str(e)}")
        return jsonify({"msg": "Something went wrong, please try again later."}), 500

@app.route('/user/data_toko/<int:id>', methods=['PUT'])
@login_role_required('user')
def update_data_toko(id):
    try:
        data_toko = DataToko.query.filter_by(id=id, user_id=session['id']).first()
        data = request.get_json()
        if not data_toko:
            return jsonify({"msg": "Data Toko tidak ditemukan"}), 404

        nama_toko = data['nama_toko']
        usia_toko = data['usia_toko']
        jenis_toko = data.get('jenis_toko')

        data_toko.nama_toko = nama_toko
        data_toko.usia_toko = usia_toko
        data_toko.jenis_toko = jenis_toko

        db.session.commit()

        return jsonify({"msg": "Data Toko berhasil diperbarui"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error: {str(e)}"}), 400
@app.route('/user/data_toko/<int:id>', methods=['DELETE'])
@login_role_required('user')
def delete_data_toko(id):
    try:
        data_toko = DataToko.query.filter_by(id=id, user_id=session['id']).first()
        
        if not data_toko:
            return jsonify({"msg": "Data Toko tidak ditemukan"}), 404

        db.session.delete(data_toko)
        db.session.commit()

        return jsonify({"msg": "Data Toko berhasil dihapus"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Error: {str(e)}"}), 400

#halaman profile
@app.route('/user/profile')
@login_role_required('user')
def profile():
    data_toko = DataToko.query.filter_by(user_id=session['id']).all()
    data = [{"id": toko.id, "nama_toko": toko.nama_toko, "usia_toko": toko.usia_toko, "jenis_toko": toko.jenis_toko} for toko in data_toko]
    return render_template('user/profile.html',data=data)

@app.route('/user/update_profile', methods=['POST'])
@login_role_required('user')
def update_profile():
    user = User.query.filter_by(id=session['id']).first()
    data = request.get_json()
    new_full_name = data.get('full_name')
    new_address = data.get('address')
    new_email = data.get('email')
    new_phone_number = data.get('phone_number')

    try:
        # Update user fields only if they are provided and different from current values
        if new_full_name and new_full_name != user.full_name:
            if User.query.filter(User.username == new_full_name, User.id != user.id).first():
                return jsonify({"msg": "nama lengkap already taken"}), 400
            if User.query.filter(User.full_name == new_full_name, User.id != user.id).first():
                return jsonify({"msg": "nama lengkap already taken"}), 400
            user.full_name = new_full_name

        if new_email and new_email != user.email:
            if user.query.filter(user.email == new_email, user.user_id != user.id).first():
                return jsonify({"msg": "Email already taken"}), 400
            user.email = new_email

        if new_address and new_address != user.address:
            user.address = new_address


        db.session.commit()

        # Update session with new data
        session['full_name'] = user.full_name
        session['address'] = user.address
        session['email'] = user.email
        data_toko = DataToko.query.filter_by(user_id=session['id']).all()
        # Cek jika data toko kosong
        if not data_toko:
            return jsonify({"msg": "Minimal tambahkan Data Toko 1 sebelum melanjutkan"}), 400

        # Check if all required fields are filled
        if not all([user.username, user.full_name, user.email]):
            return jsonify({"msg": "Silakan lengkapi semua data dahulu sebelum bisa mengakses fitur-fitur kami"}), 400

        return jsonify({"msg": "Profil berhasil diperbarui"})

    except IntegrityError as e:
        db.session.rollback()
        error_message = str(e.orig)  # Extract the original error message
        return jsonify({"msg": f"Error: {error_message}"}), 400
    except Exception as e:
        db.session.rollback()
        error_message = str(e)
        return jsonify({"msg": f"Error: {error_message}"}), 400

@app.route('/ganti_password')
@login_role_required('user')
def ganti_password():
    return render_template('ganti_password.html')

@app.route('/ganti_password', methods=["POST"])
@login_role_required('user')
def ganti_password_post():
    # Coba ambil data dari JSON
    data = request.get_json()
    if data:
        password_lama = data.get('password_lama')
        password_baru = data.get('password_baru')
    else:
        # Jika tidak ada data JSON, ambil dari form
        password_lama = request.form('password_lama')
        password_baru = request.form('password_baru')
    user = User.query.filter_by(username=session['username']).first()
    if user:
        if bcrypt.check_password_hash(user.password, password_lama):
            # Mengganti password lama dengan password baru
            user.password = bcrypt.generate_password_hash(password_baru).decode('utf-8')
            db.session.commit()
            return jsonify({"msg": "Berhasil Update Password"})
        else:
            return jsonify({"msg": "Password lama salah"})
    else:
        return jsonify({"msg": "user tidak ditemukan"})

@app.route('/user/hasil_diagnosa/<id>')
@login_role_required('user')
def user_hasil_diagnosa(id):
    if 'full_name' not in session:
        abort(403)  # Forbidden, user tidak terautentikasi

    # Query data history berdasarkan id dan username dari session
    history_record = History.query.filter_by(id=id).first()
    if not history_record:
        abort(404)  # Not found, data history tidak ditemukan
    
    # Pastikan hasil_diagnosa adalah dictionary
    hasil_diagnosa_str = history_record.hasil_diagnosa

    hasil_diagnosa = hasil_diagnosa_str.split(",")

    if hasil_diagnosa[-1] == '':
        hasil_diagnosa.pop()
    print(hasil_diagnosa)
    # Query semua rekomendasi
    rekomendasi_records = Rekomendasi.query.all()
    print(rekomendasi_records)
    rekomendasi_list = [record.serialize() for record in rekomendasi_records]
    print(rekomendasi_list)

    # Gabungkan rekomendasi yang relevan dengan hasil diagnosa
    rekomendasi_diagnosa = {}
    for deteksi in hasil_diagnosa:
        for rekomendasi in rekomendasi_list:
            if rekomendasi['nama'] == deteksi:
                rekomendasi_diagnosa[deteksi] = rekomendasi
    print(rekomendasi_diagnosa)
    # Query semua rekomendasi
    user = User.query.filter_by(id=history_record.user_id).first()
    #data_toko = DataToko.query.filter_by(id=history_record.datatoko_id).first()
    diagnosa = {
        'nama_user': user.full_name,
        # 'nama_toko': data_toko.nama_toko,
        # 'usia_toko': data_toko.usia_toko,
        'tanggal_konsultasi': history_record.tanggal_konsultasi,
        'file_deteksi': history_record.file_deteksi,
        'hasil_diagnosa': hasil_diagnosa,
        'rekomendasi_diagnosa': rekomendasi_diagnosa,
    }
    print(diagnosa)

    return render_template('user/hasil_diagnosa.html', diagnosa=diagnosa)

@app.route('/user/history_konsultasi', methods=['GET'])
@login_role_required('user')
def user_history_konsultasi():
    filter_date = request.args.get('filterDate')
    filter_month = request.args.get('filterMonth')
    filter_year = request.args.get('filterYear')
    filter_complete_date = request.args.get('filterCompleteDate')
    filter_anything = request.args.get('filteranything')  # Filter baru untuk "apapun"

    # Generate list of years from 2000 to current year
    current_year = datetime.now().year
    years = list(range(2000, current_year + 1))

    # List of months with values 1-12 in Indonesian
    months = [
        {"name": "Januari", "value": 1},
        {"name": "Februari", "value": 2},
        {"name": "Maret", "value": 3},
        {"name": "April", "value": 4},
        {"name": "Mei", "value": 5},
        {"name": "Juni", "value": 6},
        {"name": "Juli", "value": 7},
        {"name": "Agustus", "value": 8},
        {"name": "September", "value": 9},
        {"name": "Oktober", "value": 10},
        {"name": "November", "value": 11},
        {"name": "Desember", "value": 12},
    ]

    query = History.query.filter_by(user_id=session["id"])

    if filter_complete_date:
        query = query.filter(func.date(History.tanggal_konsultasi) == filter_complete_date)
    else:
        if filter_date:
            query = query.filter(extract('day', History.tanggal_konsultasi) == filter_date)
        if filter_month:
            query = query.filter(extract('month', History.tanggal_konsultasi) == filter_month)
        if filter_year:
            query = query.filter(extract('year', History.tanggal_konsultasi) == filter_year)
    
    # Aliased untuk tabel-tabel yang ingin di-join
    data_toko_alias = aliased(DataToko)
    user_alias = aliased(User)

    if filter_anything:
        query = query.join(data_toko_alias, History.datatoko_id == data_toko_alias.id)\
                    .join(user_alias, History.user_id == user_alias.id)\
                    .filter(
            db.or_(
                data_toko_alias.nama_toko.ilike(f'%{filter_anything}%'),
                data_toko_alias.usia_toko.ilike(f'%{filter_anything}%'),
                History.tanggal_konsultasi.ilike(f'%{filter_anything}%'),
                History.hasil_diagnosa.ilike(f'%{filter_anything}%'),
                user_alias.full_name.ilike(f'%{filter_anything}%')
            )
        )
    
    histori_records = query.all()
    diagnosa_records = []

    for history_record in histori_records:
        data_toko = DataToko.query.filter_by(id=history_record.datatoko_id).first()
        diagnosa = {
            'id': history_record.id,
            'nama_user': session["full_name"],
            'nama_toko': data_toko.nama_toko if data_toko else "Data Toko Tidak Ditemukan",
            'usia_toko': data_toko.usia_toko if data_toko else "N/A",
            'tanggal_konsultasi': history_record.tanggal_konsultasi.strftime('%Y-%m-%d'),
            'hasil_diagnosa': history_record.hasil_diagnosa,
        }
        diagnosa_records.append(diagnosa)
    
    return render_template('user/history_konsultasi.html', 
                           histori_records=diagnosa_records, 
                           years=years, 
                           months=months)

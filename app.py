from flask import g, Flask, request, render_template, redirect, url_for, send_file, abort, jsonify
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from werkzeug.utils import secure_filename
from elasticapm.contrib.flask import ElasticAPM
from celery import Celery
import os, datetime, logging

import lukso_utils
from captcha import ImageCaptcha
from nft_doc import NFTDoc
from user import User
from feedback import Feedback
from elastic import Elastic
from form import *
from announcement import Announcement
from common import Common
from config import Config
from lukso import Lukso
import db, security, file_util, nft_util, trophy
from flask_bootstrap import Bootstrap5

# env = {'DEV', 'LIVE'}
site_env = 'DEV'

if site_env == 'LIVE':
    db_url = 'postgres://127.0.0.1:5432/mainnet'
else:
    db_url = 'postgres://127.0.0.1:5432/testnet'

conf = Config(site_env, db_url)
site_version = '1.0.0'
site_title = conf.get('site_name') + ' v' + site_version
acquire_period = 13
app = Flask(__name__)
app.config['SECRET_KEY'] = conf.get('secret_key')
app.config['WTF_CSRF_SECRET_KEY'] = conf.get('csrf_key')
# app.config['ELASTIC_APM'] = {
#    'SERVICE_NAME': conf.get('site_name'),
#    'ELASTIC_APM_SERVICE_VERSION': site_version,
#    'ELASTIC_APM_DISABLE_METRICS': None,
#    'ELASTIC_APM_BREAKDOWN_METRICS': True
# }
app.config['CELERY_broker_url'] = 'redis://localhost:6379/0'
app.config['result_backend'] = 'redis://localhost:6379/0'
app.jinja_env.globals['apply_markup'] = nft_util.apply_markup
app.jinja_env.globals['generate_token'] = nft_util.generate_token
app.jinja_env.globals['pretty_size'] = file_util.pretty_size
app.jinja_env.globals['pretty_time'] = file_util.pretty_time
app.jinja_env.globals['site_title'] = site_title
# apm = ElasticAPM(app, logging=logging.WARNING)
login_manager = LoginManager(app)
es_nft = Elastic(index_name=conf.get('index_name'))
captcha = ImageCaptcha()
bootstrap = Bootstrap5(app)
lukso = Lukso(3000)
celery = Celery(app.name, broker=app.config['CELERY_broker_url'])
celery.conf.update(app.config)


# app.jinja_env.globals['menu_items'] = menuItems
@app.template_filter('format_balance')
def format_balance(value):
    if value is None:
        return ""
    return '{0:.4f}'.format(value).rstrip('0').rstrip('.')


@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def celery_new_nft(self, name, url, description, symbol, creator):
    with app.app_context():
        self.update_state(state='UPLOADING_METADATA', meta={'details': {}})
        meta = lukso.upload_metadata(name, url, description)
        self.update_state(state='METADATA_UPLOADED', meta={'details': meta})
        lsp7 = lukso.new_lsp7(name, symbol, creator, meta)
        self.update_state(state='LSP7_CREATED', meta={'details': lsp7})
        minted = lukso.mint_lsp8(creator, lsp7['address'])
        self.update_state(state='LSP8_MINTED', meta={'details': minted})
        import db
        conn = db.get_connection(db_url)
        conn.cursor().execute('UPDATE nft SET lsp7=%s WHERE id=%s;', (lsp7['address'], url[19:]))
        conn.close()
        self.update_state(state='DB_UPDATED', meta={'details': minted})
        return {'details': minted}


@app.route('/status_new_nft/<task_id>')
def status_new_nft(task_id):
    task = celery_new_nft.AsyncResult(task_id)
    response = {
        'state': task.state,
        'details': task.info.get('details', 'error'),
    }
    return jsonify(response)


@celery.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def celery_purchase(self, up, lsp7):
    with app.app_context():
        self.update_state(state='MINTING_LSP7', meta={'details': {}})
        minted = lukso.mint_lsp7(up, lsp7)
        self.update_state(state='LSP7_MINTED', meta={'details': minted})
        return {'details': minted}


@app.route('/status_purchase/<task_id>')
def status_purchase(task_id):
    task = celery_purchase.AsyncResult(task_id)
    response = {
        'state': task.state,
        'details': task.info.get('details', 'error'),
    }
    return jsonify(response)


@app.route('/transaction', methods=['GET'])
def transaction():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        ip = request.environ['REMOTE_ADDR']
    else:
        ip = request.environ['HTTP_X_FORWARDED_FOR']
    if ip != '127.0.0.1':
        return jsonify({'result': 'access forbidden (' + ip + ')'})
    else:
        print(request.args.get('amount'))
        print(request.args.get('sender').lower())
        g.cur.execute('UPDATE users SET balance=balance+%s WHERE id=%s;',
                      (request.args.get('amount'), request.args.get('sender').lower()))
        return jsonify({'result': 'ok'})


@app.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('user', id=current_user.get_id()))
        else:
            return render_template('pages/auth/auth-parallax.html',
                                   reg=conf.get('registration_status'))


@app.route('/user/<id>', strict_slashes=False)
@app.route('/user/<id>/<custom_from>')
@login_required
def user(id, custom_from=1):
    custom_from = int(custom_from)
    user = User().get(id.lower())
    if user is None:
        return render_template('pages/message.html',

                               message='User not found.',
                               anchor_text='Return Home',
                               anchor=url_for('index')), 404
    else:
        if custom_from < 1:
            custom_from = 1
        if custom_from * conf.get('row_per_page') > conf.get('max_result_window'):
            custom_from = int(conf.get('max_result_window') / conf.get('row_per_page'))
        nfts = es_nft.get_user_nfts(user=user.get_id(),
                                    custom_size=conf.get('row_per_page'),
                                    custom_from=custom_from - 1)
        g.cur.execute('SELECT biography FROM users WHERE id=%s;',
                      (user.get_id(),))
        biography = g.cur.fetchone()[0]
        return render_template('pages/profile.html',

                               user=user,
                               nfts=nfts,
                               biography=biography,
                               trophies=trophy.get_trophies(user.get_id()),
                               custom_from=custom_from,
                               row_per_page=conf.get('row_per_page'),
                               max_result_window=conf.get('max_result_window'))


@app.route('/top-up', strict_slashes=False)
@login_required
def top_up():
    return render_template('pages/top_up.html', receive_address=conf.get('receive_address'))


@app.route('/purchase', methods=['POST'])
@login_required
def purchase():
    form = PurchaseForm()
    if not form.validate_on_submit():
        return render_template('pages/message.html',

                               message='Can\'t purchase.',
                               anchor_text='Return Home',
                               anchor=url_for('index'))
    id = form.nft_id.data
    g.cur.execute('SELECT price FROM purchase WHERE user_id=%s AND nft_id=%s;',
                  (current_user.get_id(), id))
    old_price = g.cur.fetchone()
    if old_price is not None:
        return render_template('pages/message.html',

                               message='Already purchased at ' + str(old_price[0]) + ' LYX.',
                               anchor_text='View NFT',
                               anchor=url_for('nft', id=id))
    else:
        g.cur.execute('SELECT price, owner, lsp7 FROM nft WHERE id=%s;', (id,))
        price_owner = g.cur.fetchone()
        if price_owner is not None:
            if price_owner[1] == current_user.get_id():
                return render_template('pages/message.html',

                                       message='You\'re the owner of this NFT. Something went wrong.',
                                       anchor_text='View NFT',
                                       anchor=url_for('nft', id=id))
            elif price_owner[2] is None:
                return render_template('pages/message.html',
                                       message='NFT is still pending blockchain validation. Please try again in a few minutes.',
                                       anchor_text='View NFT',
                                       anchor=url_for('nft', id=id))
            else:
                g.cur.execute('SELECT balance FROM users WHERE id=%s;', (current_user.get_id(),))
                balance = g.cur.fetchone()[0]
                if balance >= price_owner[0]:
                    g.cur.execute('UPDATE users SET balance=balance-%s WHERE id=%s;',
                                  (price_owner[0], current_user.get_id()))
                    g.cur.execute('INSERT INTO purchase (user_id, nft_id, price) VALUES (%s, %s, %s);',
                                  (current_user.get_id(), id, price_owner[0]))
                    g.cur.execute('UPDATE users SET balance=balance+%s WHERE id=%s;',
                                  (price_owner[0], price_owner[1]))
                    # LUKSO mint LSP-7 for user's UP
                    task = celery_purchase.apply_async((current_user.get_id(), price_owner[2]))
                    return render_template('pages/message.html',

                                           message='Purchased for ' + str(format_balance(price_owner[0])) + ' LYX.',
                                           anchor_text='View NFT',
                                           anchor=url_for('nft', id=id))
                else:
                    return render_template('pages/message.html',

                                           message='You can\'t afford this NFT.',
                                           anchor_text='View NFT',
                                           anchor=url_for('nft', id=id))
        else:
            return render_template('pages/message.html',

                                   message='NFT not found.',
                                   anchor_text='Return Home',
                                   anchor=url_for('index')), 404


@app.route('/nft/<id>')
@login_required
def nft(id):
    upload_form = UploadForm()
    feedback_from = FeedbackForm()
    purchase_form = PurchaseForm(nft_id=id)
    feedback_obj = Feedback()
    preview = None
    user_status = 'BUYER'
    g.cur.execute(
        'SELECT owner, price, name, status, preview_of, description, last_edit_time, lsp7 FROM nft WHERE id=%s;',
        (id,))
    the_nft = g.cur.fetchone()
    if the_nft is None:
        return render_template('pages/message.html',

                               message='NFT not found.',
                               anchor_text='Return Home',
                               anchor=url_for('index')), 404
    else:
        if the_nft[3] == 'PREVIEW':
            g.cur.execute('SELECT name FROM nft WHERE id=%s;',
                          (the_nft[4],))
            name = g.cur.fetchone()[0]
            user_status = 'PURCHASER'
        else:
            feedback_obj.calculate_feedback(id)
            name = the_nft[2]
            preview = nft_util.get_preview_id(id)
        if current_user.get_id() == the_nft[0]:
            user_status = 'OWNER'
        elif the_nft[3] != 'PREVIEW':
            g.cur.execute(
                'SELECT price, honesty_feedback, quality_feedback FROM purchase WHERE nft_id=%s AND user_id=%s;',
                (id, current_user.get_id()))
            price_feedback = g.cur.fetchone()
            if price_feedback is not None:
                user_status = 'PURCHASER'
                feedback_from.honesty.data = nft_util.honesty_feedback_reversal(price_feedback[1])
                feedback_from.quality.data = nft_util.quality_feedback_reversal(price_feedback[2])
    g.cur.execute(
        'SELECT file_nft.file_hash, file_nft.file_name, file.size, file.creation_time, file.path, file.type_general FROM file_nft, file WHERE file_nft.file_hash = file.hash AND file_nft.status=%s AND file_nft.nft_id=%s ORDER BY file.creation_time DESC;',
        ('ACTIVE', id))
    files = g.cur.fetchall()
    g.cur.execute('SELECT  name '
                  'FROM universal_profiles WHERE id = %s;', (the_nft[0],))
    up = g.cur.fetchone()
    owner_name = up[0]
    return render_template('pages/nft.html',

                           files=files,
                           id=id,
                           upload_form=upload_form,
                           feedback_from=feedback_from,
                           user_status=user_status,
                           nft_status=the_nft[3],
                           owner=the_nft[0],
                           owner_name=owner_name,
                           price=the_nft[1],
                           name=name,
                           preview_of=the_nft[4],
                           preview=preview,
                           feedback_obj=feedback_obj,
                           description=the_nft[5],
                           last_edit_time=the_nft[6],
                           lsp7=the_nft[7],
                           purchase_form=purchase_form)


@app.route('/file/<hash>')
@login_required
def file(hash):
    g.cur.execute(
        'SELECT nft_id FROM purchase WHERE user_id=%s AND nft_id IN (SELECT nft_id FROM file_nft WHERE file_hash=%s) UNION SELECT nft.id FROM nft, file_nft WHERE nft.id=file_nft.nft_id AND nft.status=%s and file_nft.file_hash=%s;',
        (current_user.get_id(), hash, 'PREVIEW', hash))
    nfts = g.cur.fetchone()
    if nfts is not None:
        g.cur.execute(
            'SELECT file.path, file.size, file_nft.file_name FROM file, file_nft WHERE file.hash=file_nft.file_hash AND file.hash=%s;',
            (hash,))
        file = g.cur.fetchone()
        if file is not None:
            g.cur.execute(
                'SELECT release_time from acquire WHERE user_id=%s AND file_hash=%s AND release_time > NOW();',
                (current_user.get_id(), hash))
            release_time = g.cur.fetchone()
            if release_time is None:
                g.cur.execute(
                    'INSERT INTO acquire (user_id, file_hash, release_time) VALUES (%s, %s, NOW() + INTERVAL %s HOUR);',
                    (current_user.get_id(), hash, str(acquire_period)))
            else:
                g.cur.execute(
                    'UPDATE acquire SET download_count=download_count+1 WHERE user_id=%s AND file_hash=%s AND release_time=%s;',
                    (current_user.get_id(), hash, release_time[0]))
            return send_file(file[0], as_attachment=True, attachment_filename=file[2])
        else:
            return render_template('pages/message.html',

                                   message='File not found. Something went wrong.',
                                   anchor_text='Return Home',
                                   anchor=url_for('index')), 404
    else:
        # NEXT VERSION: you can't afford the transportation fee to acquire this file
        return render_template('pages/message.html',

                               message='First purchase the file\'s NFT',
                               anchor_text='Return Home',
                               anchor=url_for('index'))


@app.route('/get_login_message', methods=['POST'])
def get_login_message():
    content = request.get_json(silent=True)
    address = content.get('address')
    return jsonify(lukso_utils.get_sign_message(address))  # read 'message' from json


@app.route('/check_login', methods=['POST'])
def check_login():
    login_result = {
        "is_successful": None,
        "user_id": None,
    }
    content = request.get_json(silent=True)
    signature = content.get('signature')
    address = content.get('address').lower()
    user = address
    is_valid = lukso_utils.check_signature(signature, address)
    if is_valid:
        g.cur.execute('SELECT id FROM users WHERE id=%s',
                      (user,))
        the_user = g.cur.fetchone()
        if the_user is not None and the_user[0]:
            login_user(User().get(user))
        else:
            if conf.get('registration_status') == 'OPEN' and security.can_create_user(user):

                up_data = lukso_utils.get_user_profile(user)
                # Save Universal Profile Data in DB
                try:
                    profile_image = up_data['value']['LSP3Profile']['profileImage'][3]['url']
                except:
                    profile_image = "ipfs://QmfFFpHVWBa16J7iJTv9DfCEPVPGKYUgkwNDbwEPxneBdQ"
                truncated_user = user[0:5] + '...' + user[-5:]
                g.cur.execute(
                    'INSERT INTO universal_profiles (id, name, description, profile_image_url ) '
                    'VALUES (%s, %s,  %s, %s);',
                    (user, up_data['value']['LSP3Profile'].get("name", "") or truncated_user,
                     up_data['value']['LSP3Profile'].get("description", "") or None,
                     profile_image))
                # Add User in DB
                g.cur.execute('INSERT INTO users (id, balance, prestige) VALUES (%s, %s, %s);',
                              (user, 0, 3))
            else:
                login_result["is_successful"] = False

        login_user(User().get(user))
        g.cur.execute('UPDATE users SET last_login_time=current_login_time WHERE id=%s;', (user,))
        g.cur.execute('UPDATE users SET current_login_time=NOW() WHERE id=%s;', (user,))
        login_result["user_id"] = current_user.get_id()
        login_result["is_successful"] = True
    else:
        login_result["user_id"] = None
        login_result["is_successful"] = False
        return 'failed to verify'
    return jsonify(login_result)


@app.route('/new_nft', methods=['POST', 'GET'])
@login_required
def new_nft():
    if current_user.get_prestige() < -3:
        return render_template('pages/message.html',

                               message='You cannot create a new nft right now. It is a temporary restriction.',
                               anchor_text='Return Home',
                               anchor=url_for('index'))
    form = NFTForm()
    # form.status.data = 'ACTIVE'
    if request.method == 'GET':
        if current_user.get_prestige() < 2 and conf.get('captcha_status') == 'ENABLED':
            puzzle = captcha.get_json()
            form.puzzle.data = ImageCaptcha.get_puzzle_id(puzzle)
            form.captcha.label = ImageCaptcha.get_question(puzzle)
            form.captcha.choices = ImageCaptcha.get_options(puzzle)
        return render_template('pages/new_nft.html',

                               form=form,
                               captcha=conf.get('captcha_status'))
    elif request.method == 'POST':
        if form.validate_on_submit():
            if current_user.get_prestige() < 2:
                answer_arr = []
                if form.captcha.data is not None:
                    for answer in form.captcha.data:
                        answer_arr.append(answer)
                if conf.get('captcha_status') == 'ENABLED':
                    is_correct_answer = captcha.check(form.puzzle.data, ','.join(answer_arr))
                else:
                    is_correct_answer = True
            else:
                is_correct_answer = True
            if is_correct_answer:
                if security.nft_name_is_not_duplicate(current_user.get_id(), nft_util.strip_whitespace(form.name.data),
                                                      0):
                    msg_nft_limit = security.msg_nft_limit(current_user.get_id(), current_user.get_prestige())
                    if msg_nft_limit == 'allowed':
                        msg_price_rational = security.msg_price_rational(current_user.get_prestige(), form.price.data)
                        if msg_price_rational == 'rational':
                            g.cur.execute(
                                'INSERT INTO nft (owner, name, price, description) VALUES (%s, %s, %s, %s) RETURNING id;',
                                (current_user.get_id(),
                                 nft_util.strip_whitespace(form.name.data),
                                 form.price.data,
                                 nft_util.strip_whitespace(form.description.data)))
                            new_id = g.cur.fetchone()
                            g.cur.execute('INSERT INTO purchase (user_id, nft_id, price) VALUES (%s, %s, %s);',
                                          (current_user.get_id(), new_id[0], 0))
                            es_nft.index(body=NFTDoc(id=new_id[0],
                                                     owner=current_user.get_id(),
                                                     name=nft_util.strip_whitespace(form.name.data),
                                                     description=nft_util.strip_whitespace(form.description.data),
                                                     price=form.price.data,
                                                     status='ACTIVE',
                                                     creation_time=datetime.datetime.now(),
                                                     preview_of=None).get_nft(), id=new_id[0])
                            # LUKSO create new LSP-7 with user's UP as beneficiary and mint LSP-8
                            task = celery_new_nft.apply_async((
                                nft_util.strip_whitespace(form.name.data),
                                'luksense.store/nft/' + str(new_id[0]),
                                nft_util.strip_whitespace(form.description.data),
                                nft_util.strip_whitespace(form.name.data).upper(),
                                current_user.get_id()))
                            return redirect(url_for('nft', id=new_id[0]))
                        else:
                            return render_template('pages/message.html',

                                                   message=msg_price_rational,
                                                   anchor_text='New NFT',
                                                   anchor=url_for('new_nft'))
                    else:
                        return render_template('pages/message.html',

                                               message=msg_nft_limit,
                                               anchor_text='Return Home',
                                               anchor=url_for('index'))
                else:
                    return render_template('pages/message.html',

                                           message='You already have an NFT with same name.',
                                           anchor_text='New NFT',
                                           anchor=url_for('new_nft'))
            else:
                return render_template('pages/message.html',

                                       message='Incorrect Captcha answer.',
                                       anchor_text='Try again',
                                       anchor=url_for('new_nft'))
        else:
            if current_user.get_prestige() < 2 and conf.get('captcha_status') == 'ENABLED':
                puzzle = captcha.get_json()
                form.puzzle.data = ImageCaptcha.get_puzzle_id(puzzle)
                form.captcha.label = ImageCaptcha.get_question(puzzle)
                form.captcha.choices = ImageCaptcha.get_options(puzzle)
            return render_template('pages/new_nft.html',

                                   form=form,
                                   captcha=conf.get('captcha_status'))


@app.route('/edit_nft/<id>', methods=['POST', 'GET'])
@login_required
def edit_nft(id):
    form = EditNFTForm()
    g.cur.execute('SELECT owner, name, price, description FROM nft WHERE id=%s AND status!=%s;',
                  (id, 'PREVIEW'))
    nft = g.cur.fetchone()
    if nft is None:
        return render_template('pages/message.html',

                               message='NFT not found.',
                               anchor_text='Return Home',
                               anchor=url_for('index')), 404
    else:
        if nft[0] != current_user.get_id():
            return render_template('pages/message.html',

                                   message='Only the owner can edit this NFT.',
                                   anchor_text='View NFT',
                                   anchor=url_for('nft', id=id)), 403
        if request.method == 'GET':
            form.name.data = nft[1]
            form.price.data = nft[2]
            form.description.data = nft[3]
            return render_template('pages/edit_nft.html',

                                   form=form,
                                   id=id)
        elif request.method == 'POST':
            if form.validate_on_submit():
                new_name = nft_util.strip_whitespace(form.name.data)
                new_price = form.price.data
                new_description = nft_util.strip_whitespace(form.description.data)
                if nft[1] == new_name and nft[2] == new_price and nft[3] == new_description:
                    return render_template('pages/message.html',

                                           message='No change detected.',
                                           anchor_text='View NFT',
                                           anchor=url_for('nft', id=id))
                if not security.nft_name_is_not_duplicate(current_user.get_id(), new_name, id):
                    return render_template('pages/message.html',

                                           message='You already have an NFT with the same name.',
                                           anchor_text='Edit NFT',
                                           anchor=url_for('edit_nft', id=id))
                msg_price_rational = security.msg_price_rational(current_user.get_prestige(), new_price)
                if msg_price_rational != 'rational':
                    return render_template('pages/message.html',

                                           message=msg_price_rational,
                                           anchor_text='Edit NFT',
                                           anchor=url_for('edit_nft', id=id))
                msg_edit_limit = security.msg_edit_limit(id, current_user.get_prestige())
                if msg_edit_limit != 'allowed':
                    return render_template('pages/message.html',

                                           message=msg_edit_limit,
                                           anchor_text='View NFT',
                                           anchor=url_for('nft', id=id))
                g.cur.execute('UPDATE nft SET name=%s, price=%s, description=%s, last_edit_time=NOW() WHERE id=%s;',
                              (new_name, new_price, new_description, id))
                es_nft.update(body=NFTDoc(name=new_name, description=new_description,
                                          price=new_price).edit_nft(), id=id)
                g.cur.execute(
                    'INSERT INTO nft_edit_history (nft_id, reason, previous_name, previous_description, previous_price) VALUES (%s, %s, %s, %s, %s)',
                    (id, nft_util.strip_whitespace(form.reason.data), nft[1], nft[3], nft[2]))
                return render_template('pages/message.html',

                                       message='Changes successfully applied to the NFT.',
                                       anchor_text='View NFT',
                                       anchor=url_for('nft', id=id))
            else:
                return render_template('pages/edit_nft.html',

                                       form=form,
                                       id=id)


@app.route('/edit_history/<id>', methods=['GET'])
@login_required
def edit_history(id):
    g.cur.execute(
        'SELECT edit_time, reason, previous_name, previous_description, previous_price FROM nft_edit_history WHERE nft_id=%s ORDER BY edit_time DESC;',
        (id,))
    edits = g.cur.fetchall()
    if len(edits) == 0:
        return render_template('pages/message.html',

                               message='Edit history not available.',
                               anchor_text='Return Home',
                               anchor=url_for('index'))
    g.cur.execute('SELECT id, name, description, price, creation_time FROM nft WHERE id=%s;',
                  (id,))
    the_nft = g.cur.fetchone()
    return render_template('pages/edit_history.html',

                           edits=edits,
                           nft=the_nft)


@app.route('/upload/<id>', methods=['POST'])
@login_required
def upload(id):
    if current_user.get_prestige() < -3:
        return render_template('pages/message.html',

                               message='You cannot upload a new file right now. It is a temporary restriction.',
                               anchor_text='Return Home',
                               anchor=url_for('index'))
    form = UploadForm()
    error_string = ''
    if form.validate_on_submit():
        file_list = request.files.getlist(form.files.name)
        upload_dir = os.path.join(conf.get('storage_location'),
                                  datetime.date.today().strftime('%y%m'),
                                  datetime.date.today().strftime('%d'))
        if not os.path.isdir(upload_dir):
            os.makedirs(upload_dir)
        new_file_counter = 0
        if security.can_upload_file(current_user.get_id(), id, len(file_list)):
            for each_file in file_list:
                new_file_counter += nft_util.upload_and_process_form(file_data=each_file.stream.read(),
                                                                     file_name=each_file.filename,
                                                                     upload_dir=upload_dir,
                                                                     nft_id=id,
                                                                     es=es_nft)
            if len(file_list) - new_file_counter == 0:
                m = 'Upload was successful.'
            else:
                m = 'Upload was successful. Duplicates have been merged.'
            return render_template('pages/message.html',

                                   message=m,
                                   anchor_text='View NFT',
                                   anchor=url_for('nft', id=id))
        else:
            return render_template('pages/message.html',

                                   message='Can\'t upload more than 666 files.',
                                   anchor_text='View NFT',
                                   anchor=url_for('nft', id=id))
    else:
        error_string += str(form.files.errors)
        return render_template('pages/message.html',

                               message='Validation error: ' + error_string,
                               anchor_text='View NFT',
                               anchor=url_for('nft', id=id))


@app.route('/purchased', strict_slashes=False)
@app.route('/purchased/<custom_from>')
@login_required
def purchased(custom_from=1):
    custom_from = int(custom_from)
    if custom_from < 1:
        custom_from = 1
    if custom_from * conf.get('row_per_page') > conf.get('max_result_window'):
        custom_from = int(conf.get('max_result_window') / conf.get('row_per_page'))
    g.cur.execute(
        'SELECT COUNT(nft.id) FROM nft, purchase WHERE owner!=%s AND purchase.user_id=%s AND nft.id = purchase.nft_id AND nft.status!=%s;',
        (current_user.get_id(), current_user.get_id(), 'PREVIEW'))
    total = g.cur.fetchone()
    g.cur.execute(
        'SELECT nft.id FROM nft, purchase WHERE owner!=%s AND purchase.user_id=%s AND nft.id = purchase.nft_id AND nft.status!=%s ORDER BY purchase.purchase_time DESC LIMIT %s OFFSET %s;',
        (current_user.get_id(), current_user.get_id(), 'PREVIEW', conf.get('row_per_page'),
         (custom_from - 1) * conf.get('row_per_page')))
    ids = g.cur.fetchall()
    ids = list(map(lambda n: n[0], ids))
    nfts = es_nft.get_purchased_nfts(ids)
    return render_template('pages/purchased.html',
                           user=user,

                           total=total[0],
                           nfts=nfts,
                           custom_from=custom_from,
                           row_per_page=conf.get('row_per_page'),
                           max_result_window=conf.get('max_result_window'))


@app.route('/nft_stats/<id>')
@login_required
def nft_stats(id):
    g.cur.execute('SELECT COUNT(*) FROM purchase WHERE nft_id=%s;', (id,))
    purchase_count = g.cur.fetchone()
    if purchase_count[0] > 0:
        g.cur.execute('SELECT name, owner, status FROM nft WHERE id=%s;', (id,))
        name_owner_status = g.cur.fetchone()
        if name_owner_status[2] == 'PREVIEW':
            return render_template('pages/message.html',

                                   message='Statistics page is not available for preview nfts.',
                                   anchor_text='View Preview',
                                   anchor=url_for('nft', id=id)), 403
        g.cur.execute(
            'SELECT purchase.user_id, purchase.price, purchase.purchase_time FROM nft, purchase WHERE purchase.nft_id=%s AND purchase.user_id!=nft.owner AND nft.id=purchase.nft_id ORDER BY purchase.purchase_time DESC LIMIT 69;',
            (id,))
        users = g.cur.fetchall()
        g.cur.execute(
            'SELECT SUM(price), AVG(price), MIN(price), MAX(price) FROM purchase WHERE nft_id=%s AND user_id!=%s;',
            (id, name_owner_status[1]))
        price_table = g.cur.fetchone()
        return render_template('pages/nft_stats.html',

                               id=id,
                               users=users,
                               price_table=price_table,
                               purchase_count=purchase_count[0] - 1,
                               name=name_owner_status[0],
                               owner=name_owner_status[1])
    else:
        return render_template('pages/message.html',

                               message='NFT not found.',
                               anchor_text='Return Home',
                               anchor=url_for('index')), 404


@app.route('/enable_preview/<id>')
@login_required
def enable_preview(id):
    g.cur.execute('SELECT name, owner FROM nft WHERE id=%s AND status!=%s;', (id, 'PREVIEW'))
    name_owner = g.cur.fetchone()
    if name_owner is not None:
        if name_owner[1] == current_user.get_id():
            g.cur.execute('SELECT id FROM nft WHERE preview_of=%s;', (id,))
            preview_id = g.cur.fetchone()
            if preview_id is None:
                g.cur.execute('INSERT INTO nft (owner, status, preview_of) VALUES (%s, %s, %s) RETURNING id;',
                              (name_owner[1], 'PREVIEW', id))
                new_preview_id = g.cur.fetchone()
                return render_template('pages/message.html',

                                       message='Preview enabled for ' + name_owner[0] + '.',
                                       anchor_text='View Preview',
                                       anchor=url_for('nft', id=new_preview_id[0]))
            else:
                return render_template('pages/message.html',

                                       message='This nft already has a preview.',
                                       anchor_text='View Preview',
                                       anchor=url_for('nft', id=preview_id[0]))
        else:
            return render_template('pages/message.html',

                                   message='Only the owner can enable preview.',
                                   anchor_text='View NFT',
                                   anchor=url_for('nft', id=id)), 401
    else:
        return render_template('pages/message.html',

                               message='NFT not found.',
                               anchor_text='Return Home',
                               anchor=url_for('index')), 404


@app.route('/edit_biography', methods=['POST', 'GET'])
@login_required
def edit_biography():
    form = EditBiographyForm()
    g.cur.execute('SELECT biography FROM users WHERE id=%s;',
                  (current_user.get_id(),))
    former_biography = g.cur.fetchone()[0]
    if request.method == 'GET':
        form.biography.data = former_biography
        return render_template('pages/edit_biography.html',

                               form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            new_biography = nft_util.strip_whitespace(form.biography.data)
            if new_biography != former_biography:
                g.cur.execute('UPDATE users SET biography=%s WHERE id=%s;',
                              (new_biography, current_user.get_id()))
                return render_template('pages/message.html',

                                       message='Biography changed successfully.',
                                       anchor_text='Return Home',
                                       anchor=url_for('index'))
            else:
                return render_template('pages/message.html',

                                       message='No change detected.',
                                       anchor_text='Return Home',
                                       anchor=url_for('index'))
        else:
            return render_template('pages/edit_biography.html',

                                   form=form)


@app.route('/rate_nft/<id>', methods=['POST'])
@login_required
def rate_nft(id):
    form = FeedbackForm()
    if form.validate_on_submit():
        g.cur.execute('SELECT name, owner FROM nft WHERE id=%s AND status!=%s;', (id, 'PREVIEW'))
        name_owner = g.cur.fetchone()
        if name_owner is not None:
            if name_owner[1] == current_user.get_id():
                return render_template('pages/message.html',

                                       message='You can\'t rate your own NFTs.',
                                       anchor_text='View NFT',
                                       anchor=url_for('nft', id=id))
            else:
                g.cur.execute('SELECT honesty_feedback, quality_feedback FROM purchase WHERE nft_id=%s AND user_id=%s;',
                              (id, current_user.get_id()))
                feedback = g.cur.fetchone()
                if feedback is not None:
                    if security.can_rate_nft(current_user.get_id()):
                        g.cur.execute(
                            'UPDATE purchase SET honesty_feedback=%s, quality_feedback=%s WHERE nft_id=%s AND user_id=%s;',
                            (nft_util.honesty_feedback_check(form.honesty.data),
                             nft_util.quality_feedback_check(form.quality.data),
                             id, current_user.get_id()))
                        fb = Feedback()
                        fb.calculate_feedback(id)
                        nft_doc = NFTDoc(id=id)
                        nft_doc.set_feedback(fb)
                        es_nft.update(body=nft_doc.rate_nft(), id=id)
                        return render_template('pages/message.html',

                                               message='Rating submitted successfully.',
                                               anchor_text='View NFT',
                                               anchor=url_for('nft', id=id))
                    else:
                        return render_template('pages/message.html',

                                               message='Sorry, your prestige must be greater than zero to be able to rate NFTs.',
                                               anchor_text='View NFT',
                                               anchor=url_for('nft', id=id))
                else:
                    return render_template('pages/message.html',

                                           message='You should purchase the NFT first!',
                                           anchor_text='View NFT',
                                           anchor=url_for('nft', id=id))
        else:
            return render_template('pages/message.html',

                                   message='NFT not found.',
                                   anchor_text='Return Home',
                                   anchor=url_for('index')), 404
    else:
        return render_template('pages/message.html',

                               message='There is a problem with your inputs.',
                               anchor_text='View NFT',
                               anchor=url_for('nft', id=id)), 403


@app.route('/add_to_preview', methods=['POST', 'GET'])
def add_to_preview():
    is_bad_request = False
    if request.method == 'GET':
        file_id = request.args.get('file')
        nft_id = request.args.get('nft')
        file_name = None
        if len(file_id) != 69:
            is_bad_request = True
        try:
            nft_id = int(nft_id)
        except:
            is_bad_request = True
        try:
            g.cur.execute('SELECT file_name FROM file_nft WHERE file_hash=%s AND nft_id=%s;',
                          (file_id, nft_id))
            file_name = g.cur.fetchone()[0]
        except:
            is_bad_request = True
        if is_bad_request:
            return render_template('pages/message.html',

                                   message='There is a problem with your inputs.',
                                   anchor_text='Return Home',
                                   anchor=url_for('index')), 403
        msg = 'You\'re about to add "' + str(file_name) + '" from nft #' + str(nft_id) + \
              ' to its preview. Once it\'s added, you can\'t remove it. Are you sure?'
        form = AddToPreviewForm()
        form.nft_id.data = nft_id
        form.file_id.data = file_id
        return render_template('pages/add_to_preview.html',

                               message=msg,
                               form=form,
                               nft_id=nft_id)
    elif request.method == 'POST':
        form = AddToPreviewForm()
        nft_id = form.nft_id.data
        file_id = form.file_id.data
        file_name = None
        #
        if len(file_id) != 69:
            is_bad_request = True
        try:
            nft_id = int(nft_id)
        except:
            is_bad_request = True
        g.cur.execute('SELECT owner FROM nft WHERE id=%s;', (nft_id,))
        owner = g.cur.fetchone()
        if owner is None or len(owner) < 1 or owner[0] != current_user.get_id():
            is_bad_request = True
        try:
            g.cur.execute('SELECT file_name FROM file_nft WHERE file_hash=%s AND nft_id=%s;',
                          (file_id, nft_id))
            file_name = g.cur.fetchone()[0]
        except:
            is_bad_request = True
        if nft_util.is_preview(nft_id):
            is_bad_request = True
        if is_bad_request:
            return render_template('pages/message.html',

                                   message='There is a problem with your inputs.',
                                   anchor_text='Return Home',
                                   anchor=url_for('index')), 403
        #
        preview_id = nft_util.get_preview_id(nft_id)
        if preview_id is None:
            return render_template('pages/message.html',

                                   message='Please enable preview first.',
                                   anchor_text='View NFT',
                                   anchor=url_for('nft', id=nft_id))
        if security.can_upload_file(current_user.get_id(), preview_id, 1):
            g.cur.execute('SELECT nft_id, file_hash FROM file_nft WHERE nft_id=%s AND file_hash=%s;',
                          (preview_id, file_id))
            duplicate_file = g.cur.fetchone()
            if duplicate_file is None:
                g.cur.execute('INSERT INTO file_nft (nft_id, file_hash, file_name) VALUES (%s, %s, %s);',
                              (preview_id, file_id, file_name))
                nft_doc = NFTDoc(id=nft_id)
                nft_doc.set_preview_files(nft_util.get_files(preview_id))
                es_nft.update(body=nft_doc.upload_preview_files(), id=nft_id)
                return render_template('pages/message.html',

                                       message='Your file has been successfully added to preview.',
                                       anchor_text='View Preview',
                                       anchor=url_for('nft', id=preview_id))
            else:
                return render_template('pages/message.html',

                                       message='This file is already in the preview.',
                                       anchor_text='View NFT',
                                       anchor=url_for('nft', id=nft_id))
        else:
            return render_template('pages/message.html',

                                   message='Can\'t upload more than 666 files.',
                                   anchor_text='View NFT',
                                   anchor=url_for('nft', id=nft_id))


@app.route('/announcement/<id>', methods=['GET'])
@login_required
def announcement(id):
    g.cur.execute('SELECT id, title, creation_time, html FROM announcement WHERE id=%s;', (id,))
    tmp = g.cur.fetchone()
    the_announcement = Announcement(tmp[0], tmp[1], tmp[2], tmp[3])
    g.cur.execute('UPDATE users SET last_login_time=NOW() WHERE id=%s;', (current_user.get_id(),))
    return render_template('pages/announcement.html',
                           id=id,
                           announcement=the_announcement)


@app.route('/announcements', methods=['GET'])
@login_required
def announcements():
    g.cur.execute('SELECT id, title, creation_time FROM announcement ORDER BY creation_time DESC LIMIT 13;')
    tmp_list = g.cur.fetchall()
    the_announcements = []
    for tmp in tmp_list:
        the_announcements.append(Announcement(tmp[0], tmp[1], tmp[2]))
    g.cur.execute('UPDATE users SET last_login_time=NOW() WHERE id=%s;', (current_user.get_id(),))
    return render_template('pages/announcements.html',

                           announcements=the_announcements)


@app.route('/help', methods=['GET'])
@login_required
def help():
    help_dic = {}
    g.cur.execute('SELECT name, level, COUNT(*) FROM trophy WHERE level > 0 GROUP BY name, level;')
    help_dic['trophy_stat'] = trophy.TrophyStat(g.cur.fetchall())
    return render_template('pages/help.html',

                           help_dic=help_dic)


@app.route('/faq')
def faq():
    return render_template('pages/faq.html',
                           c=Common(current_user))


@app.route('/search_arbiter', methods=['POST'])
def search_arbiter():
    form = SearchForm()
    appendix = ''
    if form.file_type.data is not None:
        if 0 < len(form.file_type.data) < 5:
            appendix += '_'
            for file_type in form.file_type.data:
                if file_type == 'v':
                    appendix += 'v'
                if file_type == 'p':
                    appendix += 'p'
                if file_type == 'd':
                    appendix += 'd'
                if file_type == 'a':
                    appendix += 'a'
                if file_type == 'o':
                    appendix += 'o'
    return redirect(url_for('latest_nfts',
                            custom_from=1,
                            mode=form.mode.data + appendix,
                            raw_query=form.raw_query.data))


@app.route('/latest_nfts', strict_slashes=False)
@app.route('/latest_nfts/<custom_from>', strict_slashes=False)
@app.route('/latest_nfts/<custom_from>/<mode>', strict_slashes=False)
@app.route('/latest_nfts/<custom_from>/<mode>/<raw_query>')
def latest_nfts(custom_from=1, mode='default', raw_query=None):
    custom_from = int(custom_from)
    if custom_from < 1:
        custom_from = 1
    if custom_from * conf.get('row_per_page') > conf.get('max_result_window'):
        custom_from = int(conf.get('max_result_window') / conf.get('row_per_page'))
    user_query = security.prune_query(raw_query)
    print('user_query', user_query)
    mode = mode.lower()
    appendix = ''
    if '_' in mode:
        appendix = mode.split('_')[1]
        mode = mode.split('_')[0]
    if mode == 'free':
        nfts = es_nft.get_recently_updated_free(custom_size=conf.get('row_per_page'),
                                                custom_from=custom_from - 1,
                                                user_query=user_query,
                                                file_types=appendix)
    elif mode == 'top':
        nfts = es_nft.get_recently_updated_top(custom_size=conf.get('row_per_page'),
                                               custom_from=custom_from - 1,
                                               user_query=user_query,
                                               file_types=appendix)
    elif mode == 'preview':
        nfts = es_nft.get_recently_updated_with_preview(custom_size=conf.get('row_per_page'),
                                                        custom_from=custom_from - 1,
                                                        user_query=user_query,
                                                        file_types=appendix)
    else:
        nfts = es_nft.get_recently_updated(custom_size=conf.get('row_per_page'),
                                           custom_from=custom_from - 1,
                                           user_query=user_query,
                                           file_types=appendix)
    choices = []
    if 'v' in appendix:
        choices.append('v')
    if 'p' in appendix:
        choices.append('p')
    if 'd' in appendix:
        choices.append('d')
    if 'a' in appendix:
        choices.append('a')
    if 'o' in appendix:
        choices.append('o')
    selected = ChoiceObj('file_type', choices)
    sf = SearchForm(obj=selected, raw_query=user_query, mode=mode)
    sf.file_type.choices = [('v', 'Video'), ('p', 'Photo'), ('d', 'Document'), ('a', 'Archive'), ('o', 'Other')]
    if len(appendix) > 0:
        appendix = '_' + appendix
    return render_template('pages/latest_nfts.html',
                           nfts=nfts,
                           custom_from=custom_from,
                           row_per_page=conf.get('row_per_page'),
                           max_result_window=conf.get('max_result_window'),
                           mode=mode,
                           appendix=appendix,
                           user_query=user_query,
                           form=sf)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.before_request
def before_request():
    db.global_connect(db_url)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'cur'):
        g.cur.close()
    if hasattr(g, 'db'):
        g.db.close()


@login_manager.user_loader
def load_user(id):
    return User().get(id)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('pages/message.html',

                           message='Error 404: Not found',
                           anchor_text='Return Home',
                           anchor=url_for('index')), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template('pages/message.html',

                           message='Access forbidden.',
                           anchor_text='Return Home',
                           anchor=url_for('index')), 403


@app.errorhandler(401)
def unauthorized(e):
    return render_template('pages/message.html',

                           message='You\'re not authorized.',
                           anchor_text='Return Home',
                           anchor=url_for('index')), 401


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('pages/message.html',

                           message='Something went wrong.',
                           anchor_text='Return Home',
                           anchor=url_for('index')), 500


if __name__ == '__main__':
    app.run(debug=True)

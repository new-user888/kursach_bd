# app.py

from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import config

app = Flask(__name__)
app.config.from_object(config.Config)
db = SQLAlchemy(app)

# --- Models (corresponding to the provided schema) ---

class Equipment(db.Model):
    __tablename__ = 'equipment'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(255))
    name = db.Column(db.String(255))
    status = db.Column(db.String(50))
    lastmaintenancedate = db.Column(db.Date)
    # Relationship: an equipment can have many maintenance plans
    maintenance_plans = db.relationship('MaintenancePlan', backref='equipment', cascade="all, delete")

class TOROEvent(db.Model):
    __tablename__ = 'toro_event'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    description = db.Column(db.Text)
    # Relationship: an event can be part of many maintenance plans
    maintenance_plans = db.relationship('MaintenancePlan', backref='event', cascade="all, delete")

class MaintenancePlan(db.Model):
    __tablename__ = 'maintenance_plan'
    id = db.Column(db.Integer, primary_key=True)
    equipmentid = db.Column(db.Integer, db.ForeignKey('equipment.id', ondelete='CASCADE'))
    eventid = db.Column(db.Integer, db.ForeignKey('toro_event.id', ondelete='CASCADE'))
    periodicity = db.Column(db.String(50))
    # Relationships: a plan has many needs and completed works
    needs = db.relationship('Need', backref='maintenance_plan', cascade="all, delete")
    completed_works = db.relationship('CompletedWork', backref='maintenance_plan', cascade="all, delete") 

class MaterialAsset(db.Model):
    __tablename__ = 'material_assets'
    id = db.Column(db.Integer, primary_key=True)
    materialname = db.Column(db.String(255))
    price = db.Column(db.Numeric(10, 2))

class Need(db.Model):
    __tablename__ = 'needs'
    id = db.Column(db.Integer, primary_key=True)
    maintenanceplanid = db.Column(db.Integer, db.ForeignKey('maintenance_plan.id', ondelete='CASCADE'))
    materialassetid = db.Column(db.Integer, db.ForeignKey('material_assets.id', ondelete='CASCADE'))
    quantity = db.Column(db.Integer)
    # Relationship: a need links a plan and a material asset
    material_asset = db.relationship('MaterialAsset', backref='needs')

class CompletedWork(db.Model):
    __tablename__ = 'completed_work'
    id = db.Column(db.Integer, primary_key=True)
    maintenanceplanid = db.Column(db.Integer, db.ForeignKey('maintenance_plan.id', ondelete='CASCADE'))
    completion_date = db.Column(db.Date)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# --- Routes for Equipment ---

@app.route('/equipment')
def list_equipment():
    equipments = Equipment.query.all()
    return render_template('equipment_list.html', equipments=equipments)

@app.route('/equipment/create', methods=['GET', 'POST'])
def create_equipment():
    if request.method == 'POST':
        eq = Equipment(
            type=request.form['type'],
            name=request.form['name'],
            status=request.form['status'],
            lastmaintenancedate=datetime.strptime(request.form['lastmaintenancedate'], '%Y-%m-%d').date()
                if request.form['lastmaintenancedate'] else None
        )
        db.session.add(eq)
        db.session.commit()
        return redirect(url_for('list_equipment'))
    return render_template('equipment_form.html', equipment=None)

@app.route('/equipment/<int:id>/edit', methods=['GET', 'POST'])
def edit_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    if request.method == 'POST':
        equipment.type = request.form['type']
        equipment.name = request.form['name']
        equipment.status = request.form['status']
        equipment.lastmaintenancedate = datetime.strptime(request.form['lastmaintenancedate'], '%Y-%m-%d').date() \
            if request.form['lastmaintenancedate'] else None
        db.session.commit()
        return redirect(url_for('list_equipment'))
    return render_template('equipment_form.html', equipment=equipment)

@app.route('/equipment/<int:id>/delete', methods=['POST'])
def delete_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    db.session.delete(equipment)
    db.session.commit()
    return redirect(url_for('list_equipment'))

# --- Routes for TORO_Event (named "Events" in UI) ---

@app.route('/events')
def list_events():
    events = TOROEvent.query.all()
    return render_template('events_list.html', events=events)

@app.route('/events/create', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        ev = TOROEvent(
            name=request.form['name'],
            description=request.form['description']
        )
        db.session.add(ev)
        db.session.commit()
        return redirect(url_for('list_events'))
    return render_template('events_form.html', event=None)

@app.route('/events/<int:id>/edit', methods=['GET', 'POST'])
def edit_event(id):
    event = TOROEvent.query.get_or_404(id)
    if request.method == 'POST':
        event.name = request.form['name']
        event.description = request.form['description']
        db.session.commit()
        return redirect(url_for('list_events'))
    return render_template('events_form.html', event=event)

@app.route('/events/<int:id>/delete', methods=['POST'])
def delete_event(id):
    event = TOROEvent.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for('list_events'))

# --- Routes for MaintenancePlan ---

@app.route('/plans')
def list_plans():
    plans = MaintenancePlan.query.all()
    return render_template('plans_list.html', plans=plans)

@app.route('/plans/create', methods=['GET', 'POST'])
def create_plan():
    equipments = Equipment.query.all()
    events = TOROEvent.query.all()
    if request.method == 'POST':
        plan = MaintenancePlan(
            equipmentid=request.form['equipmentid'],
            eventid=request.form['eventid'],
            periodicity=request.form['periodicity']
        )
        db.session.add(plan)
        db.session.commit()
        return redirect(url_for('list_plans'))
    return render_template('plans_form.html', plan=None, equipments=equipments, events=events)

@app.route('/plans/<int:id>/edit', methods=['GET', 'POST'])
def edit_plan(id):
    plan = MaintenancePlan.query.get_or_404(id)
    equipments = Equipment.query.all()
    events = TOROEvent.query.all()
    if request.method == 'POST':
        plan.equipmentid = request.form['equipmentid']
        plan.eventid = request.form['eventid']
        plan.periodicity = request.form['periodicity']
        db.session.commit()
        return redirect(url_for('list_plans'))
    return render_template('plans_form.html', plan=plan, equipments=equipments, events=events)

@app.route('/plans/<int:id>/delete', methods=['POST'])
def delete_plan(id):
    plan = MaintenancePlan.query.get_or_404(id)
    db.session.delete(plan)
    db.session.commit()
    return redirect(url_for('list_plans'))

# --- Routes for MaterialAssets ---

@app.route('/assets')
def list_assets():
    assets = MaterialAsset.query.all()
    return render_template('assets_list.html', assets=assets)

@app.route('/assets/create', methods=['GET', 'POST'])
def create_asset():
    if request.method == 'POST':
        asset = MaterialAsset(
            materialname=request.form['materialname'],
            price=request.form['price']
        )
        db.session.add(asset)
        db.session.commit()
        return redirect(url_for('list_assets'))
    return render_template('assets_form.html', asset=None)

@app.route('/assets/<int:id>/edit', methods=['GET', 'POST'])
def edit_asset(id):
    asset = MaterialAsset.query.get_or_404(id)
    if request.method == 'POST':
        asset.materialname = request.form['materialname']
        asset.price = request.form['price']
        db.session.commit()
        return redirect(url_for('list_assets'))
    return render_template('assets_form.html', asset=asset)

@app.route('/assets/<int:id>/delete', methods=['POST'])
def delete_asset(id):
    asset = MaterialAsset.query.get_or_404(id)
    db.session.delete(asset)
    db.session.commit()
    return redirect(url_for('list_assets'))

# --- Routes for Needs ---

@app.route('/needs')
def list_needs():
    needs = Need.query.all()
    return render_template('needs_list.html', needs=needs)

@app.route('/needs/create', methods=['GET', 'POST'])
def create_need():
    plans = MaintenancePlan.query.all()
    assets = MaterialAsset.query.all()
    if request.method == 'POST':
        need = Need(
            maintenanceplanid=request.form['maintenanceplanid'],
            materialassetid=request.form['materialassetid'],
            quantity=request.form['quantity']
        )
        db.session.add(need)
        db.session.commit()
        return redirect(url_for('list_needs'))
    return render_template('needs_form.html', need=None, plans=plans, assets=assets)

@app.route('/needs/<int:id>/edit', methods=['GET', 'POST'])
def edit_need(id):
    need = Need.query.get_or_404(id)
    plans = MaintenancePlan.query.all()
    assets = MaterialAsset.query.all()
    if request.method == 'POST':
        need.maintenanceplanid = request.form['maintenanceplanid']
        need.materialassetid = request.form['materialassetid']
        need.quantity = request.form['quantity']
        db.session.commit()
        return redirect(url_for('list_needs'))
    return render_template('needs_form.html', need=need, plans=plans, assets=assets)

@app.route('/needs/<int:id>/delete', methods=['POST'])
def delete_need(id):
    need = Need.query.get_or_404(id)
    db.session.delete(need)
    db.session.commit()
    return redirect(url_for('list_needs'))

# --- Routes for CompletedWork ---

@app.route('/completed')
def list_completed():
    completed_list = CompletedWork.query.all()
    return render_template('completed_list.html', completed_list=completed_list)

@app.route('/completed/create', methods=['GET', 'POST'])
def create_completed():
    plans = MaintenancePlan.query.all()
    if request.method == 'POST':
        work = CompletedWork(
            maintenanceplanid=request.form['maintenanceplanid'],
            completion_date=datetime.strptime(request.form['completion_date'], '%Y-%m-%d').date()
        )
        db.session.add(work)
        db.session.commit()
        return redirect(url_for('list_completed'))
    return render_template('completed_form.html', completed=None, plans=plans)

@app.route('/completed/<int:id>/edit', methods=['GET', 'POST'])
def edit_completed(id):
    completed = CompletedWork.query.get_or_404(id)
    plans = MaintenancePlan.query.all()
    if request.method == 'POST':
        completed.maintenanceplanid = request.form['maintenanceplanid']
        completed.completion_date = datetime.strptime(request.form['completion_date'], '%Y-%m-%d').date()
        db.session.commit()
        return redirect(url_for('list_completed'))
    return render_template('completed_form.html', completed=completed, plans=plans)

@app.route('/completed/<int:id>/delete', methods=['POST'])
def delete_completed(id):
    completed = CompletedWork.query.get_or_404(id)
    db.session.delete(completed)
    db.session.commit()
    return redirect(url_for('list_completed'))

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/about')
def about():
    return render_template('about.html')


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)

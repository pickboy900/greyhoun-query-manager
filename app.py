# __init__file
from flask import Flask, request, render_template, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
from flask_wtf import FlaskForm
from wtforms import widgets
from flask_migrate import Migrate
from wtforms import SelectMultipleField
from wtforms_alchemy import model_form_factory

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
                                        'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['QUERIES_PER_PAGE'] = 30
app.config['SECRET_KEY'] = 'd8h0nRnNvfO2&WP3$YH@SP8^K6ZK@nAm'

# Models
class SortingQuery(db.Model):
    __tablename__ = 'sorting_query'
    id = db.Column(db.Integer, primary_key=True)
    grade_winner = db.Column(db.Boolean, nullable=False)
    intel = db.Column(db.Boolean, nullable=False)
    lowest_split = db.Column(db.Boolean, nullable=False)
    post_pick_position = db.Column(db.Integer, info={'choices': [(i, i) for i in range(4)]}, nullable=False)
    trap = db.Column(db.Integer, info={'choices': [(i, i) for i in range(1, 7)]}, nullable=False)
    sp_forecast = db.Column(db.String(100), nullable=False)
    badges = db.Column(db.String(50), nullable=False)
    neighbours = db.Column(db.Text(256), nullable=False)
    grade = db.Column(db.String(5), nullable=False)


# Forms

BaseModelForm = model_form_factory(FlaskForm)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(cls):
        return db.session


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class FilterSortingQueriesForm(FlaskForm):
    grade_choices = [i for (i,) in SortingQuery.query.with_entities(SortingQuery.grade).distinct()]
    sp_forecast_choices = [i for (i,) in SortingQuery.query.with_entities(SortingQuery.sp_forecast).distinct()]
    badges_choices = [i for (i,) in SortingQuery.query.with_entities(SortingQuery.badges).distinct()]
    neighbours_choices = [i for (i,) in SortingQuery.query.with_entities(SortingQuery.neighbours).distinct()]
    trap_choices = [i for (i,) in SortingQuery.query.with_entities(SortingQuery.trap).distinct()]
    intel_choices = ['Yes' if i else 'No' for (i,) in SortingQuery.query.with_entities(SortingQuery.intel).distinct()]
    grade_winner_choices = ['Yes' if i else 'No' for (i,) in SortingQuery.query.with_entities(SortingQuery.grade_winner).distinct()]
    lowest_split_choices = ['Yes' if i else 'No' for (i,) in SortingQuery.query.with_entities(SortingQuery.lowest_split).distinct()]
    post_pick_position_choices = [i for (i,) in SortingQuery.query.with_entities(SortingQuery.post_pick_position).distinct()]
    neighbours = MultiCheckboxField('Neighbours', choices=list(zip(neighbours_choices, neighbours_choices)))
    grade = MultiCheckboxField('Grades', choices=list(zip(grade_choices, grade_choices)))
    trap = MultiCheckboxField('Trap', choices=list(zip(trap_choices, trap_choices)))
    grade_winner = MultiCheckboxField('Is grade winner?', choices=list(zip(grade_choices, grade_choices)))
    lowest_split = MultiCheckboxField('Is lowest split?', choices=list(zip(lowest_split_choices, lowest_split_choices)))
    intel = MultiCheckboxField('Is Intel?', choices=list(zip(intel_choices, intel_choices)))
    post_pick_position = MultiCheckboxField('Post pick position?', choices=list(zip(post_pick_position_choices, post_pick_position_choices)))
    sp_forecast = MultiCheckboxField('Sp forecast', choices=list(zip(sp_forecast_choices, sp_forecast_choices)))
    badges = MultiCheckboxField('Badges', choices=list(zip(badges_choices, badges_choices)))


class SortingQueryForm(ModelForm):
    class Meta:
        model = SortingQuery
        field_args = {
            'intel': {'validators': []},
            'grade_winner': {'validators': []},
            'lowest_split': {'validators': []},
            # 'intel': {'validatros': []},
            # 'grade_winner': [],
            # 'lowest_split': [],
        }


# routes
@app.route('/', methods=["POST", "GET"])
def select_sorting_queries():
    filtering_data = session.get('filter_data')
    filtering_form = FilterSortingQueriesForm()
    rows = SortingQuery.query
    conds = []
    if filtering_form.validate_on_submit():
        session['filter_data'] = filtering_form.data
        # del session['filter_data']['csrf_token']
        print(session['filter_data'])
        return redirect(url_for('select_sorting_queries'))
    else:
        pass
        # print(filtering_form.errors)
    if filtering_data:
        filtering_form = FilterSortingQueriesForm(data=filtering_data)
        if filtering_data.get('grade'):
            conds.append(SortingQuery.grade.in_(filtering_data['grade']))
        if filtering_data['trap']:
            conds.append(SortingQuery.trap.in_(filtering_data['trap']))
        if filtering_data['post_pick_position']:
            conds.append(SortingQuery.post_pick_position.in_(filtering_data['post_pick_position']))
        if filtering_data['sp_forecast']:
            conds.append(SortingQuery.sp_forecast.in_(filtering_data['sp_forecast']))
        if filtering_data['badges']:
            conds.append(SortingQuery.badges.in_(filtering_data['badges']))
        if filtering_data['neighbours']:
            conds.append(SortingQuery.neighbours.in_(filtering_data['neighbours']))
        if len(filtering_data['grade_winner']) == 1:
            conds.append(SortingQuery.grade_winner == (True if filtering_data['grade_winner'][0] == 'Yes' else False))
        if len(filtering_data['lowest_split']) == 1:
            conds.append(SortingQuery.lowest_split == (True if filtering_data['lowest_split'][0] == 'Yes' else False))
        if len(filtering_data['intel']) == 1:
            conds.append(SortingQuery.intel == (True if filtering_data['intel'][0] == 'Yes' else False))
    page = request.args.get('page', 1, type=int)

    if conds:
        rows = rows.filter(*conds)
        # print(rows)
    # print(conds)
    rows = rows.paginate(page, app.config['QUERIES_PER_PAGE'], False)
    return render_template('select_sorting_queries.html', title="Sorting Queries", form=filtering_form,
                           curr_page=page, pagination=rows)


@app.route('/edit_row', methods=["POST", "GET"])
def edit_row():
    row_id = request.args.get('row_id', type=int)
    page = request.args.get('page', 1, type=int)
    row = SortingQuery.query.get(row_id)
    form = SortingQueryForm(obj=row)
    if form.validate_on_submit():
        form.populate_obj(row)
        db.session.commit()
        flash(f'row #{row_id} is changed!', category='success')
        return redirect(url_for('select_sorting_queries', page=page))
    return render_template('edit_query.html', form=form, row_id=row_id, page=page)
    pass


@app.route('/add_new_query', methods=["POST", "GET"])
def add_new_query():
    form = SortingQueryForm()
    if form.validate_on_submit():
        query = SortingQuery()
        form.populate_obj(query)
        db.session.add(query)
        db.session.commit()
        return redirect(url_for('select_sorting_queries'))
        pass
    else:
        print(form.errors)
    print(form.data)
    return render_template('add_sorting_query.html', form=form)
    pass


@app.route('/delete_row', methods=["GET"])
def delete_row():
    row_id = request.args.get('row_id', type=int)
    page = request.args.get('page', 1, type=int)
    row = SortingQuery.query.get(row_id)
    db.session.delete(row)
    db.session.commit()
    flash(f'row #{row_id} is deleted successfully', category='danger')
    return redirect(url_for('select_sorting_queries', page=page))
    # return render_template('select_sorting_queries.html', row_id=row_id)
    pass


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'SortingQuery': SortingQuery}


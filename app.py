import imp
import array as arr
import csv
from csv import writer
from urllib import response
import flask
from enum import unique
from venv import create
from flask import Flask, flash, redirect,render_template, url_for,request
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,PasswordField,BooleanField
from wtforms.validators import DataRequired,InputRequired,Email,Length
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,login_user,LoginManager,login_required,logout_user,current_user
#for fetching the api
import requests
import json
#importing the dependencies for ml model
import numpy as np
import pandas as pd
import difflib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

#add Database
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///users.db'
app.config['SECRET_KEY']='password123'
db=SQLAlchemy(app)

# Flask_Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#create the db model
class Users(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(15))
    email=db.Column(db.String(35),unique=True)
    password=db.Column(db.String(8))
    def get_id(self):
       return (self.id)
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id)) 

#create a Form class

class RegisterForm(FlaskForm):
    username=StringField('username',validators=[InputRequired()])
    email=StringField('email',validators=[InputRequired()])
    password=PasswordField('password',validators=[InputRequired(),Length(min=6,max=10)])
    submit=SubmitField('submit')

class LoginForm(FlaskForm):
    username=StringField('username',validators=[InputRequired()])
    password=PasswordField('password',validators=[InputRequired(),Length(min=6,max=10)])
    remember=BooleanField('remember me')
    submit=SubmitField('submit') 


#ml model using item-item collaborative filtering
ratings=pd.read_csv('ratings_final.csv')
movies=pd.read_csv('movies_final.csv')
ratings=pd.merge(movies,ratings)
user_ratings=ratings.pivot_table(index=['userId'],columns=['title'],values='rating')
user_ratings=user_ratings.dropna(thresh=10,axis=1).fillna(0)
#similarity matrix using pearson co-relation
item_similarity_df=user_ratings.corr(method='pearson')
#Recommendation
def get_recommendations2(movie_name):
  similar_score=item_similarity_df[movie_name]
  movie_match=similar_score[similar_score>0.1]
  movie_sorted=movie_match.sort_values(ascending=False)
  movie_sorted_name=movie_sorted.keys()
  i=1
  names=[]
  ids=[]
  return_df=pd.DataFrame(columns=['title','id'])
  i=1
  names=[]
  ids=[]
  return_df=pd.DataFrame(columns=['title','id'])
  for movie in movie_sorted_name :
     movieid_from_title=movies[movies.title==movie]['movieId'].values[0]
     if(i<7):
      names.append(movie)
      ids.append(movieid_from_title)
      i=i+1
  return_df['title']=names
  return_df['id']=ids
  return return_df



#create getting movie recommendation  after rating page
@app.route("/rate",methods=['GET','POST'])
def rate():
  if flask.request.method=='GET':
   movie_id_rat=[137113,58,57201,49521,2454,24428,1865,41154]
   movie_name_rate=["Edge of Tomorrow","Pirates of the Caribbean: Dead Man's Chest","The Lone Ranger","Man of Steel","The Chronicles of Narnia: Prince Caspian","The Avengers","Pirates of the Caribbean: On Stranger Tides","Men in Black 3"]
   movie_img_path=[]
   for i in range(8):
    m=str(movie_id_rat[i])
    req=requests.get('https://api.themoviedb.org/3/movie/'+m+'?api_key=da1557f8852896d28d8c05408c234abf')
    data=req.content
    json_data=json.loads(data)
    movie_img_path.append(json_data)
   return flask.render_template('rate.html',movie_name_rate=movie_name_rate, movie_img_path= movie_img_path,movie_id_rat=movie_id_rat)
  if flask.request.method=='POST':
    movie_name=flask.request.form['movie_name_i']
    movie_rating=flask.request.form['rating']
    movie_id=flask.request.form['movie_name_id']
    user_id=435
    user_id=user_id+1
    list1=[]
    list1.append(movie_id)
    list1.append(movie_name)
    list2=[]
    list2.append(user_id)
    list2.append(movie_id)
    list2.append(movie_rating)
    with open('movies_final.csv','a',newline='') as f_object:
      writer_object=writer(f_object)
      writer_object.writerow(list1)
    with open('ratings_final.csv','a',newline='') as m_object:
      writer_object=writer(m_object)
      writer_object.writerow(list2)
    result_final=get_recommendations2(movie_name)
    names=[]
    ids=[]
    for i in range(len(result_final)):
       names.append(result_final.iloc[i][0])
       ids.append(result_final.iloc[i][1])
    movie=[]
    for i in range(6):
       s=str(ids[i])
       req=requests.get('https://api.themoviedb.org/3/movie/'+s+'?api_key=da1557f8852896d28d8c05408c234abf')
       data=req.content
       json_data=json.loads(data)
       movie.append(json_data)
    return flask.render_template('user_preference.html',movie_names=names,movie=movie)

#create registeration page
@app.route("/Registeration",methods=['GET','POST'])
def Registeration():
     form=RegisterForm()
     if form.validate_on_submit():
        user=Users.query.filter_by(email=form.email.data).first()
        if user is None:
            hashed_password=generate_password_hash(form.password.data,method='sha256')
            user=Users(username=form.username.data,email=form.email.data,password=hashed_password)
            db.session.add(user)
            db.session.commit()
            form.username.data=''
            form.email.data=''
            flash("Registered Successfuly")
            return redirect(url_for('rate'))
        else :
            flash("This user already exist . Try to Register with another email ,username and password")
     return flask.render_template('Registeration.html',form=form) 

#creating login page
@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=Users.query.filter_by(username=form.username.data).first()
        if user:
            #check the hash
            if check_password_hash(user.password,form.password.data):
               login_user(user,remember=form.remember.data)
               flash('login Successfully')
               return redirect(url_for('rate'))
            else:
                flash('Wrong Password-Try Again !')
        else:
             flash('User does not exist- Register Yourself !')
    return render_template('login.html',form=form)

#creating logout page
@app.route('/logout',methods=['Get','POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

#ml model for content based filtering using cosine similarity
movies_data=pd.read_csv('./csv_files/movies.csv')
selected_features=['genres','keywords','tagline','cast','director']
for feature in selected_features:
  movies_data[feature]=movies_data[feature].fillna('')
combined_features=movies_data['genres']+' '+movies_data['keywords']+' '+movies_data['tagline']+' '+movies_data['cast']+' '+movies_data['director']
vectorizer=TfidfVectorizer()
feature_vectors=vectorizer.fit_transform(combined_features)

#getting the similarity score using cosine similarity
similarity=cosine_similarity(feature_vectors)

#function for Recommendation
def Get_Recommendation(movie_name):
    list_of_all_titles=movies_data['title'].tolist()
    find_close_match=difflib.get_close_matches(movie_name,list_of_all_titles)
    close_match=find_close_match[0]
    index_of_movie=movies_data[movies_data.title==close_match]['index'].values[0]
    similarity_score=list(enumerate(similarity[index_of_movie]))
    #Sorting the movies on the basis of their similarity score
    sorted_similar_movies=sorted(similarity_score,key=lambda x:x[1], reverse=True)
    i=1
    names=[]
    ids=[]
    overviews=[]
    return_df=pd.DataFrame(columns=['title','id'])
    for movie in sorted_similar_movies :
     index=movie[0]
     title_from_index=movies_data[movies_data.index==index]['title'].values[0]
     overview_from_index=movies_data[movies_data.index==index]['overview'].values[0]
     movie_id_from_index=movies_data[movies_data.index==index]['id'].values[0]
     if(i<7):
      names.append(title_from_index)
      ids.append(movie_id_from_index)
      overviews.append(overview_from_index)
     i=i+1
    return_df['title']=names
    return_df['id']=ids
    return_df['overview']=overviews
    return return_df
    

#setting up the main root
@app.route("/",methods=['GET','POST'])
def index():
  if flask.request.method=='GET':
    return(flask.render_template('index.html'))
  if flask.request.method=='POST':
     movie_name=flask.request.form['movie_name']
     result_final=Get_Recommendation(movie_name)
     names=[]
     ids=[]
     overview=[]
     for i in range(len(result_final)):
       names.append(result_final.iloc[i][0])
       ids.append(result_final.iloc[i][1])
       overview.append(result_final.iloc[i][2])
     movie=[]
     for i in range(6):
       s=str(ids[i])
       req=requests.get('https://api.themoviedb.org/3/movie/'+s+'?api_key=da1557f8852896d28d8c05408c234abf')
       data=req.content
       json_data=json.loads(data)
       movie.append(json_data)
     return flask.render_template('positive.html',movie_names=names,movie=movie,overview=overview,movie_name=movie_name)

if __name__=="__main__":
 app.run(debug=True)
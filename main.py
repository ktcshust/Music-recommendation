import sys
from PyQt5.QtWidgets import *
import pandas as pd
import numpy as np
import pyodbc
import spotipy
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from sklearn.metrics.pairwise import cosine_similarity
from spotipy.oauth2 import SpotifyClientCredentials
from PyQt5.QtGui import QIntValidator

spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="7e5c4955d03c412482338a09edc225b6",
                                                                client_secret="4ebbedb4f6554c6a9c1252e053866a82"))




from PyQt5.QtCore import *

class PandasModel(QAbstractTableModel):
    def __init__(self, df):
        QAbstractTableModel.__init__(self)
        self._data = df

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return QVariant(str(self._data.values[index.row()][index.column()]))
        return QVariant()

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            return QVariant(str(self._data.columns[section]))
        else:
            return QVariant(str(section + 1))

class Recommender:
    def __init__(self):
        # Initialize the DataFrames from SQL Server
        self.user_df = pd.DataFrame()
        self.rating_df = pd.DataFrame()
        self.song_df = pd.DataFrame()
        self.username = None
        self.password = None

    # Screen new song to the song_df DataFrame, if you don't add, you can skip
    # Included 2 def add and crawler
    def add(self, x):
        # Create a box to print x
        song_link = x
        song_URI = song_link.split("/")[-1].split("?")[0]
        track_dict = spotify.track(song_URI)
        track_df = pd.DataFrame.from_dict({
            'artists': [track_dict['artists']],
            'available_markets': [track_dict['available_markets']],
            'disc_number': [track_dict['disc_number']],
            'duration_ms': [track_dict['duration_ms']],
            'explicit': [track_dict['explicit']],
            'external_urls': [track_dict['external_urls']],
            'href': [track_dict['href']],
            'id': [track_dict['id']],
            'is_local': [track_dict['is_local']],
            'name': [track_dict['name']],
            'preview_url': [track_dict['preview_url']],
            'track_number': [track_dict['track_number']],
            'type': [track_dict['type']],
            'uri': [track_dict['uri']],
            'Artist': [track_dict['artists'][0]['name']],
            'X_Uri': [track_dict['artists'][0]['uri']]
        })
        track_audio_features = spotify.audio_features(tracks=track_df['uri'].values.tolist())
        audio_features_df = pd.DataFrame.from_dict(track_audio_features)
        drop_cols = ['type', 'id', 'uri', 'track_href', 'analysis_url', 'key', 'duration_ms']
        audio_features_df.drop(columns=drop_cols, inplace=True)
        artist_df = pd.concat([track_df, audio_features_df], axis=1)
        artist_df1 = artist_df.replace(np.nan, 0)
        if len(self.song_df) == 0:
            self.song_df = artist_df1
        else:
            mask = ~self.song_df['uri'].isin(artist_df1['uri'])
            self.song_df = pd.concat([self.song_df[mask], artist_df1], ignore_index=True)
        print("Song added successfully.")

    def crawler(self, x):
        # Create a box to print x
        artist_link = x
        artist_URI = artist_link.split("/")[-1].split("?")[0]
        URI = "spotify:track:" + artist_URI
        album_uris = [z["uri"] for z in spotify.artist_albums(artist_URI)["items"]]
        df = pd.DataFrame.from_dict(spotify.album_tracks(album_uris[0])["items"])
        print('T')
        df['Artist'] = 'xyz'
        df['X_Uri'] = 'abc'
        for k in range(len(spotify.album_tracks(album_uris[0])["items"])):
            df.at[k, 'Artist'] = spotify.album_tracks(album_uris[0])["items"][k]['artists'][0]['name']
            df.at[k, 'X_Uri'] = spotify.album_tracks(album_uris[0])["items"][k]['artists'][0]['uri']
        for i in range(1, len(album_uris) - 1):
            df2 = pd.DataFrame.from_dict(spotify.album_tracks(album_uris[i])["items"])
            df2['Artist'] = 'xyz'
            df2['X_Uri'] = 'abc'
            for k in range(len(spotify.album_tracks(album_uris[i])["items"])):
                df2.at[k, 'Artist'] = spotify.album_tracks(album_uris[i])["items"][k]['artists'][0]['name']
                df2.at[k, 'X_Uri'] = spotify.album_tracks(album_uris[i])["items"][k]['artists'][0]['uri']
            df = pd.concat([df, df2], ignore_index=True)
        print('D')
        df3 = df.reset_index()
        df3.drop('index', axis=1)
        df4 = df3.drop('index', axis=1)
        track_audio_features = spotify.audio_features(tracks=df4['uri'].values.tolist())
        print('A')
        audio_features_df = pd.DataFrame.from_dict(track_audio_features)
        drop_cols = ['type', 'id', 'uri', 'track_href', 'analysis_url']
        audio_features_df.drop(columns=drop_cols, inplace=True)
        artist_df = pd.concat([df4, audio_features_df], axis=1)
        artist_df1 = artist_df.replace(np.nan, 0)
        print('B')
        if len(self.song_df) == 0:
            self.song_df = artist_df1
        else:
            mask = ~self.song_df['uri'].isin(artist_df1['uri'])
            self.song_df = pd.concat([self.song_df[mask], artist_df1], ignore_index=True)
        print("Song added successfully.")

    # Create login and signup screen, main menu to choose login and signup

    # Screen sign up for a new account, have 3 text box to print: Username, Password, Repeat Password
    def signup(self, username, password):
        if len(self.user_df) == 0:
            print('Signup')
            self.user_df = pd.DataFrame({'username': [username], 'password': [password]})
        else:
            if any(self.user_df['username'] == str(username)):
                print("Username already taken. Please choose a different username.")
            else:
                user_df1 = pd.DataFrame({'username': [username], 'password': [password]})
                print('Signup')
                self.user_df = pd.concat([self.user_df, user_df1], ignore_index = True)
                print(f"Account for {username} created successfully. Please log in to continue.")
            print(self.user_df)

    # Log in a user, go to main menu screen and return their ratings in screen backup the rating
    # Log in screen, have 2 textbox: username and password

    def log_in(self, username, password):
        if any((self.user_df['username'] == username) & (self.user_df['password'] == password)):
            self.username = username
            self.password = password
            print("Login")
        else:
            print("Incorrect username or password. Please try again.")
            # Return to this login form

    # After login, I want create a main screen with main menu, with some chosen:
    # + Go to the screen display the song_df
    # + Go to the screen to rating the song
    # + Go to the screen backup history rating of account
    # + Go to the screen to recommend similar songs based on a given song
    # + Go to the screen recommend songs based on the user's ratings and song features
    # + Log out

    # Create a screen display the song_df, textbox to display result
    def full_song(self):
        return self.song_df

    # Create a screen display the userrating, textbox to display result
    def full_rating(self):
        return self.rating_df[self.rating_df['username'] == self.username]

    # Add a rating for a song
    # Create a screen to rating the song, 2 textbox is title and rating, and a button to confirm
    # Create a screen to backup the history rating of account, in a listbox
    def add_rating(self, title, rating):
        song_link = title
        song_URI = song_link.split("/")[-1].split("?")[0]
        URI = "spotify:track:" + song_URI
        if len(self.rating_df) == 0:
            print('A')
            self.rating_df = pd.DataFrame({'username': [self.username], 'title': [title], 'rating': [rating]})
        else:
            if URI not in self.song_df['uri'].values:
                print("Song not found.")
                # Return to the add rating form
            else:
                if int(rating) < 0 or int(rating) > 100:
                    print("Rated again.")
                else:
                    rating_df1 = pd.DataFrame({'username': [self.username], 'title': [title], 'rating': [rating]})
                    self.rating_df = pd.concat([self.rating_df, rating_df1], ignore_index=True)
        return self.rating_df


    # Screen to recommend similar songs based on a given song, have one textbox is title, a confirm button and a listbox to display the result
    def get_similar_recommendations(self, title):
        X = self.song_df[['danceability', 'energy', 'valence', 'instrumentalness', 'acousticness', 'speechiness']]
        cosine_sim1 = cosine_similarity(X, X)
        indices = pd.Series(data=list(self.song_df.index), index=self.song_df['uri'])
        song_URI = title.split("/")[-1].split("?")[0]
        URI = "spotify:track:" + song_URI
        idx = indices[URI]

        sim_scores = list(enumerate(cosine_sim1[idx]))

        sim_scores.sort(key=lambda x: x[1], reverse=True)

        sim_scores = sim_scores[1:21]
        ind = []
        tit = []
        name = []
        score = []
        for (x, y) in sim_scores:
            ind.append(x)
            score.append(y)
            tit.append(self.song_df.iloc[x]['uri'])
            name.append(self.song_df.iloc[x]['name'])
        data = {'Name': name, 'Title': tit, 'Score': score}
        df = pd.DataFrame(data)
        return df

    # Screen recommend songs based on the user's ratings and song features, have a button to recommend and a listbox to display the result
    def recommend_songs(self):
        user_ratings = self.rating_df.loc[self.rating_df['username'] == self.username]
        print(user_ratings)
        self.song_df['title'] = 'https://open.spotify.com/track/' + self.song_df['id']
        print(self.song_df)
        merged_df = self.song_df.merge(user_ratings[['title', 'rating']], on='title', how='left')
        print(merged_df)
        merged_df.to_csv('demo.csv')
        rated_songs = merged_df[~merged_df['rating'].isna()]
        print(rated_songs)
        unrated_songs = song_df[merged_df['rating'].isna()]
        print(unrated_songs)

        # Calculate the similarity between the rated and unrated songs using cosine similarity
        similarity_matrix = cosine_similarity(rated_songs.iloc[:, 1:-1], unrated_songs.iloc[:, 1:-1])

        # Select the top k similar songs
        k = 10
        top_k_indices = np.argsort(similarity_matrix, axis=0)[-k:]

        # Use the ratings of the top k songs and their feature values to predict the rating of the unrated song
        predicted_ratings = []
        for i in range(unrated_songs.shape[0]):
            similarity_scores = similarity_matrix[top_k_indices[:, i], i]
            ratings = rated_songs.iloc[top_k_indices[:, i], -1]
            predicted_rating = np.dot(similarity_scores, ratings) / np.sum(similarity_scores)
            predicted_ratings.append(predicted_rating)
        

        # Add the predicted ratings to the dataframe
        unrated_songs['predicted_rating'] = predicted_ratings
        return unrated_songs
        print(unrated_songs)

    # Log out of the current account
    # Log out button in main menu of main screen
    def logout(self):
        if self.username:
            print(f"Logged out of account {self.username}.")
            self.username = None
            self.password = None
        else:
            print("No account is currently logged in.")

class MainScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.recommender = Recommender()

    def initUI(self):
        # Create a label and a text field
        label1 = QLabel('Add a song:')
        self.textField1 = QLineEdit()
        label2 = QLabel('Crawl an artist:')
        self.textField2 = QLineEdit()

        # Create a button to add a song
        addBtn = QPushButton('Add')
        addBtn.clicked.connect(self.add)

        # Create a button to crawl an artist
        crawlBtn = QPushButton('Crawl')
        crawlBtn.clicked.connect(self.crawl)
        # Create a button to skip to LoginScreen
        skipBtn = QPushButton('Skip')
        skipBtn.clicked.connect(self.switchToLoginScreen)

        # Create a vertical layout and add the widgets
        vbox = QVBoxLayout()
        vbox.addWidget(label1)
        vbox.addWidget(self.textField1)
        vbox.addWidget(addBtn)
        vbox.addWidget(crawlBtn)
        vbox.addWidget(skipBtn)

        # Set the layout and show the window
        self.setLayout(vbox)
        self.show()

        self.setWindowTitle("Add")
        self.setGeometry(100, 100, 500, 500)
    def add(self):
        # Get the text from the text field
        song = self.textField1.text()
        if 'open.spotify.com/track' not in song:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Invalid song link, please try again')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the song link text field
            self.textField1.clear()
        else:
            self.recommender.add(song)

    def crawl(self):
        # Get the text from the text field
        artist = self.textField2.text()
        if 'open.spotify.com/artist' not in artist:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Invalid artist link, please try again')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the song link text field
            self.textField2.clear()
        else:
            print('Crawl')
            self.recommender.crawler(artist)

    def switchToLoginScreen(self):
        # Switch to the LoginScreen
        self.loginScreen = LoginSignUpScreen()
        self.loginScreen.show()
        self.hide()

class LoginSignUpScreen(QMainWindow):
    def __init__(self, Recommender):
        super().__init__()

        self.initUI()
        self.recommender = Recommender

    def initUI(self):
        # Create a central widget for the main window
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a vertical layout for the central widget
        vbox = QVBoxLayout(central_widget)

        # Create a tab widget
        tab_widget = QTabWidget()

        # Create three tabs
        tab1 = QWidget()
        tab2 = QWidget()

        # Add some widgets to the first tab
        label1_1 = QLabel('Username')
        self.textField1_1 = QLineEdit()
        label1_2 = QLabel('Password')
        self.textField1_2 = QLineEdit()
        loginbutton = QPushButton('Login')
        loginbutton.clicked.connect(self.login)
        tab1.layout = QVBoxLayout(tab1)
        tab1.layout.addWidget(label1_1)
        tab1.layout.addWidget(self.textField1_1)
        tab1.layout.addWidget(label1_2)
        tab1.layout.addWidget(self.textField1_2)
        tab1.layout.addWidget(loginbutton)
        tab1.setLayout(tab1.layout)

        label2_1 = QLabel('Username')
        self.textField2_1 = QLineEdit()
        label2_2 = QLabel('Password')
        self.textField2_2 = QLineEdit()
        label2_3 = QLabel('Repeat password')
        self.textField2_3 = QLineEdit()
        signupbutton = QPushButton('Sign up')
        signupbutton.clicked.connect(self.signup)
        tab2.layout = QVBoxLayout(tab2)
        tab2.layout.addWidget(label2_1)
        tab2.layout.addWidget(self.textField2_1)
        tab2.layout.addWidget(label2_2)
        tab2.layout.addWidget(self.textField2_2)
        tab2.layout.addWidget(label2_3)
        tab2.layout.addWidget(self.textField2_3)
        tab2.layout.addWidget(signupbutton)
        tab2.setLayout(tab2.layout)

        # Add the tabs to the tab widget
        tab_widget.addTab(tab1, 'Login')
        tab_widget.addTab(tab2, 'Sign up')


        # Add the tab widget to the central widget
        vbox.addWidget(tab_widget)
        central_widget.setLayout(vbox)

        # Set the main window properties
        self.setGeometry(100, 100, 500, 500)
        self.setWindowTitle('Music Screen')
        self.show()

    

    def login(self):
        # get the entered username and password
        username = self.textField1_1.text()
        password = self.textField1_2.text()

        # check if the username and password are correct
        if username == '' or password == '':
            # go to the music screen
            # show an error message
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Please fill out the form')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the password field
            self.textField1_1.clear()   
            self.textField1_2.clear()
        else:  
            self.recommender.log_in(username, password)
            print('Login')
            if any((self.recommender.user_df['username'] == str(username)) & (self.recommender.user_df['password'] == str(password))):
                self.recommender.username = username       
                self.go_to_music_screen()
            else:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setText('Wrong username or password')
                msg_box.setWindowTitle('Error')
                msg_box.exec_()
                # clear the password field  
                self.textField1_2.clear()
    def signup(self):
        # get the entered username and password
        username = self.textField2_1.text()
        password = self.textField2_2.text()
        repeat_password = self.textField2_3.text()
        if username == '' or password == '' or repeat_password == '':
            # show an error message
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Passwords do not match')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the password and repeat password fields
            self.textField2_1.clear()
            self.textField2_2.clear()
            self.textField2_3.clear()
        else: 
            if password != repeat_password:
                # show an error message
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setText('Passwords do not match')
                msg_box.setWindowTitle('Error')
                msg_box.exec_()
                # clear the password and repeat password fields
                self.textField2_2.clear()
                self.textField2_3.clear()
          
            else:
                self.recommender.signup(username, password)
                if len(self.recommender.user_df) == 0:
                    # show an error message
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Critical)
                    msg_box.setText('Sign up successful')
                    msg_box.setWindowTitle('Success')
                    msg_box.exec_()
                else:
                    if not any(self.recommender.user_df['username'] == username):
                        # show an error message
                        msg_box = QMessageBox()
                        msg_box.setIcon(QMessageBox.Critical)
                        msg_box.setText('Sign up successful')
                        msg_box.setWindowTitle('Success')
                        msg_box.exec_()



                    else:
                        msg_box = QMessageBox()
                        msg_box.setIcon(QMessageBox.Information)
                        msg_box.setText('Username already exists')
                        msg_box.setWindowTitle('Error')
                        msg_box.exec_()
                        # clear the username, password, and repeat password fields
                        self.textField2_1.clear()
                        self.textField2_2.clear()
                        self.textField2_3.clear()
    def go_to_music_screen(self):
        self.music_screen = MusicScreen(Recommender)
        self.music_screen.show()
        self.hide()


class MusicScreen(QMainWindow):
    def __init__(self, Recommender):
        super().__init__()
        self.initUI()
        self.recommender = Recommender

    def initUI(self):
        # Create a central widget for the main window
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a vertical layout for the central widget
        vbox = QVBoxLayout(central_widget)

        # Create a tab widget
        tab_widget = QTabWidget()

        # Create three tabs
        tab1 = QWidget()
        tab2 = QWidget()
        tab3 = QWidget()
        tab4 = QWidget()

        # Add some widgets to the first tab
        label1_1 = QLabel('Enter song link')
        self.textfield1_1 = QLineEdit()
        addbutton = QPushButton('Add')
        addbutton.clicked.connect(self.add)
        label1_2 = QLabel('Enter song artist')
        self.textfield1_2 = QLineEdit()
        crawlbutton = QPushButton('Crawl')
        crawlbutton.clicked.connect(self.crawl)
        refreshbutton = QPushButton('Refresh')
        self.tableview1 = QTableView()
        refreshbutton.clicked.connect(self.full_song)
        tab1.layout = QVBoxLayout(tab1)
        tab1.layout.addWidget(label1_1)
        tab1.layout.addWidget(self.textfield1_1)
        tab1.layout.addWidget(addbutton)
        tab1.layout.addWidget(label1_2)
        tab1.layout.addWidget(self.textfield1_2)
        tab1.layout.addWidget(crawlbutton)
        tab1.layout.addWidget(refreshbutton)
        tab1.layout.addWidget(self.tableview1)
        tab1.setLayout(tab1.layout)



        # Add some widgets to the second tab
        label2_1 = QLabel('Song link')
        self.textfield2_1 = QLineEdit()
        label2_2 = QLabel('Rating')
        self.textfield2_2 = QLineEdit()
        self.textfield2_2.setValidator(QIntValidator())
        ratingbutton = QPushButton('Enter')
        ratingbutton.clicked.connect(self.rating)
        refresh2button = QPushButton('Refresh')
        refresh2button.clicked.connect(self.full_rating)
        self.tableview2 = QTableView()
        tab2.layout = QVBoxLayout(tab2)
        tab2.layout.addWidget(label2_1)
        tab2.layout.addWidget(self.textfield2_1)
        tab2.layout.addWidget(label2_2)
        tab2.layout.addWidget(self.textfield2_2)
        tab2.layout.addWidget(ratingbutton)
        tab2.layout.addWidget(refresh2button)
        tab2.layout.addWidget(self.tableview2)

        tab2.setLayout(tab2.layout)

        # Add some widgets to the third tab
        label3 = QLabel('Song link')
        self.textfield3 = QLineEdit()
        similarbutton = QPushButton('Recommend')
        similarbutton.clicked.connect(self.get_similar_recommendations)
        self.tableview3 = QTableView()
        tab3.layout = QVBoxLayout(tab3)
        tab3.layout.addWidget(label3)
        tab3.layout.addWidget(self.textfield3)
        tab3.layout.addWidget(similarbutton)
        tab3.layout.addWidget(self.tableview3)
        tab3.setLayout(tab3.layout)

        # Add some widgets to the fourth tab
        getrecbutton = QPushButton('Recommend')
        getrecbutton.clicked.connect(self.get_recommend)
        self.tableview4 = QTableView()
        tab4.layout = QVBoxLayout(tab3)
        tab4.layout.addWidget(getrecbutton)
        tab4.layout.addWidget(self.tableview4)
        tab4.setLayout(tab4.layout)

        # Add the tabs to the tab widget
        tab_widget.addTab(tab1, 'Add and crawl')
        tab_widget.addTab(tab2, 'Rating')
        tab_widget.addTab(tab3, 'Recommend')
        tab_widget.addTab(tab4, 'Predicted rating')


        # Add the tab widget to the central widget
        vbox.addWidget(tab_widget)
        central_widget.setLayout(vbox)

        # Set the main window properties
        self.setGeometry(100, 100, 500, 500)
        self.setWindowTitle('Music Screen')
        self.show()

    def add(self):
        # Get the text from the text field
        song = self.textfield1_1.text()
        if 'open.spotify.com' not in song:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Invalid song link, please try again')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the song link text field
            self.textfield1_1.clear()
        else:
            self.recommender.add(song)

    def crawl(self):
        # Get the text from the text field
        artist = self.textfield1_2.text()
        if 'open.spotify.com' not in artist:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Invalid song link, please try again')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the song link text field
            self.textfield1_2.clear()
        else:
            self.recommender.crawler(artist)

    def full_song(self):
        # get the data
        data = self.recommender.song_df
        # create a table model to display the song data in the table view
        table_model = PandasModel(data)
        self.tableview1.setModel(table_model)

    def full_rating(self):
        # get the data
        data = self.recommender.rating_df[self.recommender.rating_df['username'] == self.recommender.username]

        # create a table model to display the song data in the table view
        table_model = PandasModel(data)

        # set the table model on the table view
        self.tableview2.setModel(table_model)

    def rating(self):
        title = self.textfield2_1.text()
        rating = self.textfield2_2.text()
        if 'open.spotify.com' not in title:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Invalid song link')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the song link text field
            self.textfield2_1.clear()
        else:
            if int(rating) < 1 and int(rating) > 100:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setText('Invalid rating')
                msg_box.setWindowTitle('Error')
                msg_box.exec_()
                # clear the song link text field
                self.textfield2_2.clear()
            else:
                self.recommender.add_rating(title, rating)

    def get_similar_recommendations(self):
        # get the song link from the textfield
        song_link = self.textfield3.text()
        song_uri = song_link.split("/")[-1].split("?")[0]
        uri = "spotify:track:" + song_uri
        # check if the link is valid
        if 'open.spotify.com' not in song_link:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Invalid song link')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the song link text field
            self.song_link.clear()
        else:
            if any(self.recommender.song_df['uri'] == uri):

                self.recommender.get_similar_recommendations(song_link)
                data = self.recommender.get_similar_recommendations(song_link)

                # create a table model to display the song data in the table view
                table_model = PandasModel(data)
                self.tableview3.setModel(table_model)
            else:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setText('Song not found')
                msg_box.setWindowTitle('Error')
                msg_box.exec_()


        # create a pandas DataFrame for the similar songs


    def get_recommend(self):
        self.recommender.recommend_songs()
        # get the data
        #data = self.recommender.recommend_songs

        # create a table model to display the song data in the table view
        #table_model = PandasModel(data)

        # set the table model on the table view
        #self.tableview4.setModel(table_model)

if __name__ == "__main__":
    Recommender = Recommender()
    app = QApplication(sys.argv)
    main_screen = MusicScreen(Recommender)
    main_screen.show()
    sys.exit(app.exec_())

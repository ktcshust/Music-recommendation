import sys
from PyQt5.QtWidgets import *
import pandas as pd
import numpy as np
import pyodbc
import spotipy
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from spotipy.oauth2 import SpotifyClientCredentials

spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="7e5c4955d03c412482338a09edc225b6",
                                                                client_secret="4ebbedb4f6554c6a9c1252e053866a82"))

server = 'DESKTOP-HV2USD0\MSSQLSERVER01'
database = 'recommend'
cnxn = pyodbc.connect('DRIVER={SQL Server Native Client 11.0};'
                      f'SERVER={server};'
                      f'DATABASE={database};'
                      'Trusted_Connection=yes;')


from PyQt5.QtCore import *

class Recommender:
    def __init__(self):
        # Initialize the DataFrames from SQL Server
        self.user_df = pd.read_sql('SELECT * FROM users', cnxn)
        self.rating_df = pd.read_sql('SELECT * FROM ratings', cnxn)
        self.song_df = pd.read_sql('SELECT * FROM songs', cnxn)
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
        mask = ~self.song_df['uri'].isin(artist_df1['uri'])
        self.song_df = pd.concat([self.song_df[mask], artist_df1], ignore_index=True)
        print("Song added successfully.")
        self.song_df.to_sql('songs', cnxn, if_exists='replace', index=False)

    def crawler(self, x):
        # Create a box to print x
        artist_link = x
        artist_URI = artist_link.split("/")[-1].split("?")[0]
        URI = "spotify:track:" + artist_URI
        album_uris = [z["uri"] for z in spotify.artist_albums(artist_URI)["items"]]
        df = pd.DataFrame.from_dict(spotify.album_tracks(album_uris[0])["items"])
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
        df3 = df.reset_index()
        df3.drop('index', axis=1)
        df4 = df3.drop('index', axis=1)
        track_audio_features = spotify.audio_features(tracks=df4['uri'].values.tolist())
        audio_features_df = pd.DataFrame.from_dict(track_audio_features)
        drop_cols = ['type', 'id', 'uri', 'track_href', 'analysis_url']
        audio_features_df.drop(columns=drop_cols, inplace=True)
        artist_df = pd.concat([df4, audio_features_df], axis=1)
        artist_df1 = artist_df.replace(np.nan, 0)
        mask = ~self.song_df['uri'].isin(artist_df1['uri'])
        self.song_df = pd.concat([self.song_df[mask], artist_df1], ignore_index=True)
        print("Song added successfully.")
        self.song_df.to_sql('songs', cnxn, if_exists='replace', index=False)

    # Create login and signup screen, main menu to choose login and signup

    # Screen sign up for a new account, have 3 text box to print: Username, Password, Repeat Password
    def signup(self, username, password):

        if username in self.user_df['username'].values:
            print("Username already taken. Please choose a different username.")
            return False
            # Return to this sign up form
        else:
            self.user_df = self.user_df.append({'username': username, 'password': password}, ignore_index=True)
            self.user_df.to_sql('users', cnxn, if_exists='replace', index=False)
            print(f"Account for {username} created successfully. Please log in to continue.")
            return True

    # Log in a user, go to main menu screen and return their ratings in screen backup the rating
    # Log in screen, have 2 textbox: username and password

    def log_in(self, username, password):
        if (username in self.user_df['username'].values) and (
                password in self.user_df.loc[self.user_df['username'] == username]['password'].values):
            self.username = username
            self.password = password

        else:
            print("Incorrect username or password. Please try again.")
            return False
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

        if title not in self.song_df['uri'].values:
            print("Song not found.")
            return
            # Return to the add rating form
        else:
            if int(rating) < 0 or int(rating) > 100:
               print("Rated again.")
            else:
               if self.rating_df.empty:
                  self.rating_df = pd.DataFrame({username: [self.username], title: [title], rating: [rating]})
               else:
                  rating_df1 = pd.DataFrame({username: [self.username], title: [title], rating: [rating]})
                  self.rating_df = pd.concat([self.rating_df, rating_df1], ignore_index=True)


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
        for (x, y) in sim_scores:
            ind.append(x)
            tit.append(self.song_df.iloc[x]['uri'])
            name.append(self.song_df.iloc[x]['name'])
        return pd.Series(data=tit, index=ind, name=name)

    # Screen recommend songs based on the user's ratings and song features, have a button to recommend and a listbox to display the result
    def recommend_songs(self):
        if not self.username or not self.password:
            print("Please log in first.")
            return

        user_ratings = self.rating_df.loc[self.rating_df['username'] == self.username]

        usersong = self.song_df[self.song_df['uri'].isin(user_ratings['uri'].tolist())]
        usersong1 = usersong.reset_index(drop=True)
        usersong2 = usersong1[['danceability', 'energy', 'valence', 'instrumentalness', 'acousticness', 'speechiness']]
        userprofile = usersong2.transpose().dot(user_ratings['rating'])
        genretable = self.song_df.set_index(self.song_df['movieId'])
        genretable1 = genretable[['danceability', 'energy', 'valence', 'instrumentalness', 'acousticness', 'speechiness']]
        recommendationtable_df = ((genretable1 * userprofile).sum(axis=1)) / (userprofile.sum())
        return recommendationtable_df

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
        if 'open.spotify.com' not in song:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Invalid song link, please try again')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the song link text field
            self.song.clear()
        else:
            self.recommender.add(song)

    def crawl(self):
        # Get the text from the text field
        artist = self.textField2.text()
        if 'open.spotify.com' not in artist:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Invalid artist link, please try again')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the song link text field
            self.artist.clear()
        else:
            self.recommender.crawler(artist)

    def switchToLoginScreen(self):
        # Switch to the LoginScreen
        self.loginScreen = LoginScreen()
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
        username = self.textField1.text()
        password = self.textField2.text()

        # check if the username and password are correct
        if self.recommender.log_in(username, password):
            # go to the music screen
            self.go_to_music_screen()
            self.recommender.username = username
        else:
            # show an error message
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Wrong username or password')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the password field
            self.password.clear()
    def signup(self):
        # get the entered username and password
        username = self.textField1.text()
        password = self.textField2.text()
        repeat_password = self.textField3.text()

        # check if the password and repeat password match
        if password != repeat_password:
            # show an error message
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Passwords do not match')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the password and repeat password fields
            self.password.clear()
            self.repeat_password.clear()
            return
            # check if the username already exists
        if self.recommender.signup(username, password):
            # show a success message
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText('Sign up successful')
            msg_box.setWindowTitle('Success')
            msg_box.exec_()

            # go back to the login screen
            self.go_to_login_screen()
        else:
            # show an error message
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Username already exists')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the username, password, and repeat password fields
            self.textField1.clear()
            self.textField2.clear()
            self.textField3.clear()

    def go_to_music_screen(self):
        self.music_screen = MusicScreen()
        self.music_screen.show()
        self.hide()


class MusicScreen(QMainWindow, Recommender):
    def __init__(self):
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
        refreshbutton.clicked.connect(self.full_song)
        self.tableview1 = QTableView()
        tab1.layout = QVBoxLayout(tab1)
        tab1.layout.addWidget(label1_1)
        tab1.layout.addWidget(self.textfield1_1)
        tab1.layout.addWidget(addbutton)
        tab2.layout.addWidget(label1_2)
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
        tab4.layout.addWidget(tableview4)
        tab4.setLayout(tab4.layout)

        # Add the tabs to the tab widget
        tab_widget.addTab(tab1, 'Tab 1')
        tab_widget.addTab(tab2, 'Tab 2')
        tab_widget.addTab(tab3, 'Tab 3')
        tab_widget.addTab(tab4, 'Tab 4')


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
            self.song.clear()
            return
        self.recommender.add(song)

    def crawl(self):
        # Get the text from the text field
        artist = self.textfield1_2.text()
        if 'open.spotify.com' not in song:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Invalid song link, please try again')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the song link text field
            self.song.clear()
            return
        self.recommender.crawl(artist)

    def full_song(self):
        # get the data
        data = self.recommender.song_df
        # create a table model to display the song data in the table view
        table_model = PandasModel(data)
        self.tableview1.setModel(table_model)

    def full_rating(self):
        # get the data
        data = self.recommender.rating_df[self.recommender.rating_df['username'] == self.recommend.username]

        # create a table model to display the song data in the table view
        table_model = PandasModel(data)

        # set the table model on the table view
        self.tableview2.setModel(table_model)

    def rating(self):
        title = self.textfield2_1.text()
        rating = self.textfield2_2.text()
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
            return
        if not self.recommender.song_df['uri'].isin([uri]).any():
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('Song not found, try again')
            msg_box.setWindowTitle('Error')
            msg_box.exec_()
            # clear the song link text field
            self.song_link.clear()
            return
        # call the get_similar_recommendations function of the recommender
        similar_songs = self.recommender.get_similar_recommendations(song_link)

        # check if there are any similar songs
        if len(similar_songs) == 0:
            self.show_error_message('No similar songs found')
            return

        # create a pandas DataFrame for the similar songs
        similar_songs_df = pd.DataFrame({'Song Link': similar_songs})

        # create a table model to display the song data in the table view
        table_model = QAbstractTableModel(similar_songs_df)

        # set the table model on the table view
        tableview3 = self.tab_widget.widget(0).findChild(QTableView)
        tableview3.setModel(table_model)

    def get_recommend(self):
        # get the data
        data = self.recommender.recommendationtable_df

        # create a table model to display the song data in the table view
        table_model = QAbstractTableModel(data)

        # set the table model on the table view
        table_view = self.tab_widget.widget(0).findChild(QTableView)
        table_view.setModel(table_model)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_screen = MainScreen()
    main_screen.show()
    sys.exit(app.exec_())

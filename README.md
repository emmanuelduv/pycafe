pycafe
======

Cybercafe management in python Django for server part and py-gtk for client

Composed of 3 parts : Server, Client controler and client user interface.

The server manages users, tickets, computers...
It's a Django application and is now disigned for one cybercafe (probably extensible to many but not tested)
A ticket can be purchased for a declared user or an anonymous user. The admin declares the paid price and the amount of time allowed for this price. If the ticket is associated with a declared user, only this user will be able to connect with it.
 Adding time to an existing ticket is possible : search page exists to find a ticket knowing it's id or password (identifier)
 This transactions are saved : a transaction occurs at a date, there is a seller (cybercafe admin) and a ticket for it. Some pages lists transactions by user, date or ticket
A user consist of a login (corresponding to system user in /etc/passwd) and informations like password (to connect later to the admin site and see credit, not tested also), email, ...
A computer is declared with it's name, IP address, and the minimum of time necessary to connect : this x minutes time is used at connexion and must not be 0 because the remaining time is checked every x minutes.
3 functions exists to handle the following events and the correspônding views return JSON formatted data.
 A user connects : the function checks that connexion is possible : existing ticket & minimum amount of time, existing user (if the ticket is linked to a user) and returns the amount of time remaining plus other session informations. The session end-date is set to current date + x minutes
 A user stay connecteed : every x minutes the client calls this function. Checks and updates are like the begining of a session.
 A user disconnects : The session is closed and end-date is updated to be the reality and consumed time is also updated.

The client controller is here to be launched with high privileges in order to prevent users to kill it!. It just transfers queries from the client to the server and returns answers back to client. A special function exists to kill processes which do not belong to system users neither to users in a specified list (eg cybercafe admin)

The client is opened on session startup
 If the user did not saved ticket id and password, a fullscreen window asking for credentials is created. this window tries to detect events like "an other window is launched on the top", "the window is closed", ... to be always on the top and fuulscreen so tha user must enter credentials before using it's session.
 Then a small and discrete window is shown with remaining time and a "quit" button

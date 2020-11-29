from queue import Queue
import sqlite3

connection = sqlite3.connect("degreesofbacon.db")
connection.row_factory = sqlite3.Row
db = connection.cursor()
# Start/root is beginning point of search, rootid is the id of the root
root = None
# Error checking.  If no one with name is found
while root == None:
    root = input("Start: ")
    root = db.execute(f"SELECT id FROM people WHERE name LIKE :root;", (root,))
    rootid = db.fetchall()
    if len(rootid) == 0:  
        print("No one found with that name.")  
        root = None
rootid=[i[0] for i in rootid]
counter = 1

# If more than 1 person with that name exists
if len(rootid) > 1:
    print("There are multiple actors with that name. \n Did you mean?")
    query = "SELECT * FROM people WHERE people.id IN ({num});".format(num=','.join(['?']*len(rootid)))
    db.execute(query, list(rootid))
    list = db.fetchall()
    # For each name in the list
    for row in list:
        query = (f"SELECT title FROM media WHERE id IN ({row['knownfor']});")
        db.execute(query)
        knownfor = db.fetchall()
        # If a person shows up that is not known for any media
        if len(knownfor) == 0:
            continue
        else:
            # Display a row with a number, the name, the year they were born, and a list of media they're known for
            print(f"#{counter}: {row['name']} born in {row['birth']} known for ", end="")
            for index,element in enumerate(knownfor):
                if index == (len(knownfor) - 1):
                    print(f"{element['title']}.")
                else:    
                    print(element['title'], end=", ")
            counter += 1
    # Initiate selection to a string initially
    selection = "Pizza"
    # Error checking selection
    while type(selection) == str:
        selection = input("Selection: ")
        try:
            # Try to cast selection to an int
            selection = int(selection)
            # If selection can be casted to an int check that it's valid
            if (selection > (counter - 1) or (selection < 1)):
                selection = "Pizza"
                print("Invalid.")
            continue
        # If selection cannot be casted to an int
        except ValueError:
            print("Must enter a whole number as input.")
            continue
    rootid = list[selection - 1]['id']
else:
    # De-Listing rootid
    rootid = rootid[0]
# Target is the person you're finding the "degrees" from
target = db.execute(f'SELECT id FROM people WHERE name LIKE "Kevin Bacon";')
targetid = db.fetchall()[0]['id']
print("\n")
# Checked cached paths to speed up search
db.execute("SELECT * FROM paths WHERE root = (?) AND target = (?);", (str(rootid), str(targetid),))
cachedpath = db.fetchall()
if len(cachedpath) == 1:
    path = cachedpath[0]['path']
    path = path.strip('][').split(', ')
    degrees = cachedpath[0]['degrees']
    for i in range(0, len(path)):
        print(path[(len(path) - 1) - i].strip('"'))
        print("\u2193")
    db.execute("SELECT name FROM people WHERE id = ?;", (str(targetid),))    
    target = db.fetchall()[0]['name']
    print(target)
    print (f"\nThey are {degrees} degrees from {target}")
    quit()
# Initiating a queue for the search
q = Queue(maxsize=0)
# Add root to the queue
q.put(rootid)
# Checked is a dict of all checked id's to avoid double searching a person or infinite loops
# checked format = actor_id:parent_actor_id
checked = {rootid: None}
# Targetfound is a bool describing it's name
targetfound = 0
while targetfound == 0:
    current = q.get()
    if current == targetid:
        targetfound = 1
    else:
        db.execute("SELECT person_id FROM stars WHERE media_id IN (SELECT media_id FROM stars WHERE person_id = ?);", (str(current),))
        for row in db.fetchall():
            # "in" searches keys only
            if row['person_id'] in checked:
                continue
            else:
                checked[row['person_id']] = current
                q.put(row['person_id'])
# parent is "parent" of actor, when parent = None you have your root
parent = checked[targetid]
# path is a list of actors and movies from target to root (reverse order) in printable format
path = []
current = targetid
while parent != None:
    db.execute("SELECT title, release FROM media WHERE id = (SELECT media_id FROM stars WHERE person_id = :person AND media_id IN (SELECT media_id FROM stars WHERE person_id = :parent));", (current, parent,))
    sharedmovie = db.fetchall()[0]
    db.execute("SELECT name FROM people WHERE id = ?;", (parent,))
    person = db.fetchall()[0]['name']
    path.append(f"{person} who's in {sharedmovie['title']}({sharedmovie['release']}) with")
    current = parent
    parent = checked[current]
degrees = len(path)
db.execute("SELECT name FROM people WHERE id = ?;", (str(targetid),))
target = db.fetchall()[0]['name']
for i in range(0, len(path)):
    print(path[((len(path) - 1) - i)])
    print("\u2193")
print(target)
print(f"\nThey are {degrees} degrees from {target}")
# Cache this found path for future use
db.execute("INSERT INTO paths VALUES (?, ?, ?, ?);", (str(rootid), str(targetid), str(path), degrees))
connection.commit()
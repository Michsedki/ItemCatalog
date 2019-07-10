from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, CategoryItem, User

engine = create_engine('sqlite:///CatItem.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# # Create dummy user
User1 = User(name="guest user", email="gestuser@gmail.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()


# Menu for UrbanBurger
category1 = Category(user_id=1, name="Animals")
session.add(category1)
session.commit()

categoryItem1 = CategoryItem(user_id=1, name="dog", description="Dogs (Canis lupus familiaris) are domesticated mammals, not natural wild animals. They were originally bred from wolves. They have been bred by humans for a long time, and were the first animals ever to be domesticated. There are different studies that suggest that this happened between 15.000 and 100.000 years before our time. The dingo is also a dog, but many dingos have become wild animals again and live independently of humans in the range where they occur (parts of Australia).", category=category1)

session.add(categoryItem1)
session.commit()


category2 = Category(user_id=1, name="Cars")
session.add(category2)
session.commit()

categoryItem3 = CategoryItem(user_id=1, name="ford", description="A car (or automobile) is a wheeled motor vehicle used for transportation. Most definitions of car say they run primarily on roads, seat one to eight people, have four tires, and mainly transport people rather than goods.[2][3]Cars came into global use during the 20th century, and developed economies depend on them. The year 1886 is regarded as the birth year of the modern car when German inventor Karl Benz patented his Benz Patent-Motorwagen. Cars became widely available in the early 20th century. One of the first cars accessible to the masses was the 1908 Model T, an American car manufactured by the Ford Motor Company. Cars were rapidly adopted in the US, where they replaced animal-drawn carriages and carts, but took much longer to be accepted in Western Europe and other parts of the world.", category=category2)

session.add(categoryItem3)
session.commit()

category3 = Category(user_id=1, name="Sports")
session.add(category3)
session.commit()


category4 = Category(user_id=1, name="Tools")
session.add(category4)
session.commit()

category5 = Category(user_id=1, name="Jobs")
session.add(category5)
session.commit()


print("added Category Items!")

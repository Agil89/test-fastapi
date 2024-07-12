from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import models, schemas, crud, auth, deps, cache
from .cache import cache

app = FastAPI()

@app.post("/signup", response_model=schemas.User)
def signup(user: schemas.UserCreate, db: Session = Depends(deps.get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/login")
def login(form_data: schemas.UserCreate, db: Session = Depends(deps.get_db)):
    user = crud.get_user_by_email(db, email=form_data.email)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/addpost", response_model=schemas.Post)
def add_post(post: schemas.PostCreate, db: Session = Depends(deps.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if len(post.text.encode('utf-8')) > 1 * 1024 * 1024: 
        raise HTTPException(status_code=400, detail="Payload too large")
    return crud.create_post(db=db, post=post, user_id=current_user.id)

@app.get("/getposts", response_model=list[schemas.Post])
def get_posts(db: Session = Depends(deps.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.email in cache:
        return cache[current_user.email]
    posts = crud.get_posts(db=db, user_id=current_user.id)
    cache[current_user.email] = posts
    return posts

@app.delete("/deletepost/{post_id}", response_model=dict)
def delete_post(post_id: int, db: Session = Depends(deps.get_db), current_user: models.User = Depends(auth.get_current_user)):
    if not crud.delete_post(db=db, post_id=post_id, user_id=current_user.id):
        raise HTTPException(status_code=404, detail="Post not found")
    return {"detail": "Post deleted successfully"}

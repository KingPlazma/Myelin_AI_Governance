# Deprecated Setup Guide

This repository no longer uses Supabase for backend storage.

Use Firebase Firestore instead:
- configure `backend/.env`
- set `FIREBASE_PROJECT_ID`
- set `FIREBASE_CREDENTIALS_JSON`
- enable the `Cloud Firestore API` in Google Cloud for your Firebase project

Current setup docs:
- [README.md](./README.md)
- [QUICKSTART.md](./QUICKSTART.md)

If you are migrating an older local setup, remove any stale `SUPABASE_*` variables from your environment before starting the backend.

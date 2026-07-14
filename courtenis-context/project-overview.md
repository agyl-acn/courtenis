# Courtenis

## Overview

Courtenis is a web-based tennis court booking platform with an AI agent
as a natural language assistant. Built as a cloud workshop demo (AWS),
it demonstrates the integration of a React frontend, FastAPI backend,
AI agent (Gemini via OpenAI Agents SDK), and SQLite storage (local) —
designed to be migrated to AWS Lambda + DynamoDB + S3 + CloudFront.

Two roles exist: **User** (book courts, chat with agent) and
**Admin** (manage court data, view all bookings).

## Goals

1. A demo that feels like a real application — not just curl commands in a terminal
2. Demonstrate AI agent integration into a web app with a proper UI
3. Easy to migrate to AWS after local setup is complete (zero code changes
   to business logic)

## Core User Flow

### User
1. Open homepage, browse available courts in the featured section
2. Fill in the booking form (location, court type, date, time, duration, players)
   or click "Book Court Now" — form is sent to the AI agent
3. Agent checks availability and confirms the booking
4. User can open the chatbot (bottom-right corner) to ask questions in
   natural language: check availability, booking status, court recommendations
5. User can view their booking history

### Admin
1. Open `/admin` — summary dashboard (total bookings, courts, revenue)
2. Court CRUD — add, edit, delete courts
3. View all bookings across all users
4. Can also chat with the agent for quick queries ("how many bookings today?")

## Features

### User Features
- Homepage with hero section and booking form
- Floating chatbot (bottom-right corner) — natural language to AI agent
- Featured courts section
- User booking history

### Admin Features
- Dashboard: total bookings, active courts, today's revenue
- Court management — CRUD (name, type, price, location, capacity)
- Booking list — all bookings, filterable by date/court
- Admin can also use the chatbot for quick data queries

### AI Agent Capabilities
- Check court availability by date and time
- Create a new booking from chat
- Answer questions about existing bookings
- Recommend courts (cheapest, nearest, available)
- Query statistics for admin ("total bookings today")

## Scope

### In Scope
- React + Vite frontend (user view + admin view)
- FastAPI backend with AI agent (Gemini)
- SQLite local storage
- Two role UIs: user and admin (no auth — role selected via route)
- Floating chatbot widget connected to the agent
- Court CRUD via admin panel

### Out of Scope
- Authentication / login system (simplified for workshop)
- Payment gateway
- Email / notifications
- Multi-language support
- Mobile app
- AWS deployment (documented as "next steps", not part of this build)

## Success Criteria

1. User can book a court via the form and via the chatbot in natural language
2. Admin can add/edit/delete courts and view all bookings
3. Agent can handle at least 5 conversation use cases (check availability,
   make booking, check history, recommend court, query statistics)
4. Frontend can be built with `npm run build` producing static files
   ready to upload to S3
5. Backend can be deployed to Lambda without changing any business logic

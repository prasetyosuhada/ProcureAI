# 🛒 ProcureAI 🤖

**Phase:** MVP Development
**Focus:** Requirement Clarification & Demand Analysis

## Overview
ProcureAI is an Agentic AI system designed to help employees transform unstructured purchasing needs into a structured and justified Purchase Requisition (PR).

Instead of requiring users to understand procurement terminology and manually complete numerous fields, users can describe their needs using natural language. The system uses LLM-powered agents (LangGraph & Gemini) to:
1. Understand the user's purchasing intent.
2. Ask relevant clarification questions.
3. Transform the conversation into a structured requirement.
4. Analyze whether the requested demand is reasonable based on available organizational data.
5. Recommend the appropriate purchase quantity.
6. Generate a PR draft for user review and submission.

> **Note**: The current MVP explicitly excludes vendor sourcing, RFQ, negotiation, and PO creation.

## Repository Structure
This repository uses a monorepo structure:
- `/backend`: FastAPI server, LangGraph orchestration, AI Agents, and mock enterprise tools.
- `/frontend`: React & Tailwind CSS web application providing the chat interface.
- `/.docs`: Foundational design documents (PRD, System Architecture, Test Plan).

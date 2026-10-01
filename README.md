# AI Research Radar

A weekly agent that monitors new research on AI governance, filters it by relevance and quality, and produces two things: a newsletter-style digest for consultants and a structured Google Sheet for researchers.

## What it does

1. Searches OpenAlex for AI governance papers published in the last 7 days
2. Filters each paper for relevance (Gate 1) and quality (Gate 2)
3. Scores papers on four feasibility criteria
4. Writes a weekly digest covering everything that passed
5. Copies the top 5 papers into a Google Sheet with 20 structured fields

## Why

Staying current on AI governance research is slow. This agent reads the abstracts, judges what's worth your time, and hands you either a 3-minute digest or a searchable database — depending on how deep you want to go.

## Status

Work in progress. Currently building.

## Stack

Python, OpenAI structured outputs, Pydantic, OpenAlex API, Google Sheets API.

## Setup

(coming soon)

## Case study

(coming soon)
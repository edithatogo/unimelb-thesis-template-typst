// Minimal test that uses the full `thesis` wrapper to mirror the real document
#import "lib.typ": *

#show: thesis.with(
  title: "The Secret Life of Quantum Penguins: A Computational Analysis",
  subtitle: "How Flightless Birds Revolutionized Parallel Processing",
  author: "Dr. Archibald Featherstone",
  degree: "Doctor of Philosophy",
  department: "Department of Computing and Information Systems",
  school: "School of Engineering",
  university: "The University of Melbourne",
  supervisor: "Professor Jane Smith",
  co_supervisor: "Dr. John Doe",
  submission_date: datetime(year: 2024, month: 12, day: 15),
)

// Main body: produce enough content for a header to appear on page 2
= Introduction

#lorem(1200)

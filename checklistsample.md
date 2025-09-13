# Festival Research Checklist Sample

You will either be the top level coordinator or handling a specific subtask from the checklist below.

## Checklist

- [ ] Source

  Search the web and fetch/download web pages to find info on the given festival.
  Use curl if there is a problem with fetch webpage.

  Extract relevant information to source.md

- [ ] Core

    - [ ] USP
    
      Overall USP of this festival.

    - [ ] Anchor

      What are the ANCHOR ACTIVITIES that they're most known for, or what reviews say are highlights from this festival.

    - [ ] Motivation

      Aside from activities/activations, what in general is this festival known for?  Why is it famous?  Why do consumers/trade come to this?

    - [ ] Core Depth

      Breadth & Depth:  duration of festival.  How wide?  Who participates (e.g., includes local restaurants and businesses and if so how many local partners and how many local activations?  List out what types of local partners specifically – not generally)

    - [ ] General

      General info on # of visitors, dates of year, cities held, key highlights

- [ ] Categories

  List the categories of activities, events, brand activations, are offered.
  If categories are quite similar and will result in similar reports, you may 
  consider combining them to avoid duplicating info.

- [ ] Details

  For each category type, delegate a subtask (task id Details) (agent not specified) to research and extract the following info into the file category_[name].md:

  - [ ] Check existing
    
    First, check the dir for any existing category files that might overlap.
    If you see a likely candidate file, read it, and make sure you don't duplicate
    information in this category section.

  - [ ] DESCRIPTION

    Description of the category.

  - [ ] Examples
      
    Full list of EXAMPLES of activities within that category for that festival

  - [ ] Learning

    BEST PRACTICE or KEY LEARNING (if any) that we should emulate or take & adapt.

  - [ ] BREADTH & DEPTH

    BREADTH & DEPTH of activities within this category, such as how many days, how many locations, which are well attended, who are the vendors, variety of activities, and variety of suppliers/vendors

  - [ ] WHO

    WHO puts on which of these activities?  the event producers, local restaurants, brand/advertising sponsors, city government, associations, etc – which events by who?

  - [ ] Photos

    Photos that best exemplify the extent and scope and nature of this category of activity. If there are not sufficient images in the prepared source data, do some images/specific web searches. If necessary you can use curl to examine the specific web page source. Although generally some images should be available using the search tools. Embed photos as images in the markdown referencing their URLs.

  You can use core pre-downloaded info or web research/curl. No need to put headings in all caps (that will be handled by renderer).

  Important: if top level coordinator, when assigning these subtasks , remember to provide the absolute path to the festival dir in temp, and the name of the category in the instructions.

- [ ] Output

   Combine the output markdown files (except for source) using `cat`. Then convert that to PDF and show the full file path of the final report.

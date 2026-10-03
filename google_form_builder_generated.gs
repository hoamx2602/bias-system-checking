/**
 * GENERATED FILE — DO NOT EDIT BY HAND.
 *
 * Source of truth : google_form_v2_spec.json
 * Generator       : scripts/build_form_gs.py
 * Regenerate with : python scripts/build_form_gs.py
 *
 * Any edit made here is lost the next time the generator runs. Change the spec
 * instead, then regenerate.
 *
 * Layout follows the V2 question format — one topic per page, short questions,
 * radio buttons and checkboxes, a small grid — but the pages are categories
 * rather than scenarios. The scenario-annotation component is gone: respondents
 * are domain experts evaluating the taxonomy, not annotators applying it.
 *
 * Each category page carries its definition, dimensions and illustrative example
 * in the page description, so the reference material sits in front of the expert
 * while they answer and is never repeated elsewhere.
 *
 * Two questions replace V1's five free-text boxes per category, using the V2
 * checkbox pattern. Both yield structured, directly analysable data:
 *   Dn_MISPLACED — the category's own dimensions as checkboxes: which do not belong?
 *   Dn_OVERLAP   — the other categories as checkboxes: which does this overlap?
 * Dn_OVERLAP aggregates into a category-by-category overlap matrix, which is the
 * evidence a distinctiveness claim actually needs.
 */

const SPEC = {
  "title": "[DRAFT - DO NOT DISTRIBUTE] Expert Validation: A Hierarchical Taxonomy of Biases in Human Decision-Making",
  "sheetTitle": "[DRAFT] Expert Validation - Taxonomy Bias Responses",
  "description": "Researcher: Saima Sammad | Doctoral research / PhD | University of Bradford\nSupervisory team: Professor Hassan Ugail and Dr Kamran Mahroof\nContact: {EMAIL} | Please respond by {RETURN_BY}\n\nExpert review of a proposed taxonomy of biases in human decision-making: whether its categories are clear, relevant, distinct, comprehensive and practically usable.\n\nEach category is presented on its own page, with its definition, dimensions and an illustrative example in front of you as you answer. You review in depth only the categories you select - every category page opens with a question that lets you skip straight to the next one.\n\nMost experts review 2-4 categories, which takes about 25-35 minutes. Reviewing all ten takes 80-100 minutes.",
  "meta": {
    "researcherEmail": "[insert email address]",
    "returnBy": "[insert requested return date]",
    "retentionPeriod": "[insert retention period from the approved ethics documentation]",
    "publish": false
  },
  "ethics": {
    "dataProtection": "REPLACE BEFORE DISTRIBUTION with wording that matches the approved ethics documentation exactly.\n\nData controller: University of Bradford. Purpose: academic research as described above. Lawful basis: [insert - normally \"task in the public interest\" for university research]. Personal data collected: reviewer code, and optionally your name, role, institution, discipline and email. Retention: {RETENTION}. Storage: responses are held in Google Workspace, which may involve transfer outside the UK under approved safeguards. Withdrawal: email {EMAIL} quoting your reviewer code and your response will be deleted. Data-protection queries: [insert DPO contact].\n\nIndividual comments may be paraphrased or reported in aggregated form in accordance with the approved ethics arrangements.",
    "declarations": [
      "I understand the purpose of this expert review.",
      "I understand that participation is voluntary.",
      "I understand how my feedback will be used.",
      "I understand how to withdraw my response."
    ]
  },
  "categoryOptions": [
    "1. Personal Identity Biases",
    "2. Social and Relational Biases",
    "3. Professional and Educational Biases",
    "4. Cognitive and Psychological Biases",
    "5. Situational and Contextual Biases",
    "6. Technological and Media Biases",
    "7. Cultural and Regional Biases",
    "8. Health and Wellness Biases",
    "9. Bias Manifestations and Indicators",
    "Intersectionality (cross-cutting property)"
  ],
  "validationScale": [
    "1 — Strongly disagree",
    "2 — Disagree",
    "3 — Neither agree nor disagree",
    "4 — Agree",
    "5 — Strongly agree",
    "N/A — Cannot assess"
  ],
  "relevanceOptions": [
    "1 — Not relevant",
    "2 — Somewhat relevant",
    "3 — Quite relevant",
    "4 — Highly relevant",
    "N/A — Outside my expertise"
  ],
  "experienceBands": [
    "Under 5",
    "5–9",
    "10–14",
    "15–19",
    "20 or more"
  ],
  "gate": {
    "question": "Do you wish to review this category in detail?",
    "yes": "Yes — review this category",
    "no": "No — skip to the next category"
  },
  "validationRows": [
    "The name accurately represents the content of this category.",
    "The definition is clear and unambiguous.",
    "The listed dimensions belong in this category.",
    "The boundary with adjacent categories is sufficiently clear.",
    "The example illustrates the category well.",
    "The category is usable for annotating real decision narratives."
  ],
  "categories": [
    {
      "code": "D1",
      "title": "Category 1: Personal Identity Biases",
      "shortTitle": "Personal Identity Biases",
      "definition": "Bias arising from intrinsic or socially recognised personal identity characteristics that influence perceptions, evaluations and decision-making about individuals.",
      "dimensions": [
        "Race",
        "Ethnicity",
        "Gender",
        "Age",
        "Religion",
        "Sexual orientation",
        "National origin",
        "Socioeconomic status",
        "Language",
        "Marital status",
        "Parental status",
        "Veteran status",
        "Genetic information",
        "Legal status (e.g., citizenship, residency)"
      ],
      "example": "A hiring panel rates an equally qualified candidate lower after learning that they hold non-citizen status, despite the candidate having unrestricted permission to work.",
      "note": "Boundary note: “Socioeconomic Status” and “Marital Status”/“Parental Status” refer to an individual’s own demographic or social-position characteristics. Category 2 addresses related but distinct relational and behavioural constructs, including marital role expectations, parenting style, household composition and social-network affiliations."
    },
    {
      "code": "D2",
      "title": "Category 2: Social and Relational Biases",
      "shortTitle": "Social and Relational Biases",
      "definition": "Bias arising from social relationships, interpersonal interactions, network affiliations and perceived similarity in interests or values that influence perceptions, evaluations and decision-making.",
      "dimensions": [
        "Family responsibilities (e.g., caregiver roles)",
        "Volunteer and community engagement",
        "Social networks",
        "Peer groups",
        "Affiliations",
        "Friendship circles",
        "Marital role expectations",
        "Parenting style",
        "Household composition (e.g., single-parent, extended family)",
        "Shared hobbies and interests",
        "Pet ownership",
        "Travel and leisure preferences",
        "Personal values",
        "Philanthropic interests"
      ],
      "example": "A manager gives a high-profile assignment to an employee from the same social network because they feel more comfortable with them.",
      "note": "Boundary note: This category concerns relational standing, social connection and perceived interpersonal similarity rather than demographic status itself. Elective lifestyle and value-based dimensions are included only where they function as signals of affinity or social compatibility. Part F, Question 8 asks directly whether this consolidation is appropriate."
    },
    {
      "code": "D3",
      "title": "Category 3: Professional and Educational Biases",
      "shortTitle": "Professional and Educational Biases",
      "definition": "Bias arising from professional roles, educational backgrounds, qualifications and career-related characteristics that influence perceptions of competence, credibility or suitability.",
      "dimensions": [
        "Education",
        "Educational institution (e.g., alma mater prestige)",
        "Field of study (e.g., STEM vs. humanities)",
        "Work experience",
        "Professional title",
        "Certifications and licences",
        "Job title",
        "Industry (e.g., technology, finance, healthcare)",
        "Career path (e.g., non-linear vs. linear)",
        "Professional affiliations",
        "Employment history",
        "Professional skills",
        "Professional competencies"
      ],
      "example": "A panel rates a candidate more highly mainly because they attended a prestigious university.",
      "note": ""
    },
    {
      "code": "D4",
      "title": "Category 4: Cognitive and Psychological Biases",
      "shortTitle": "Cognitive and Psychological Biases",
      "definition": "Bias arising from psychological characteristics, cognitive tendencies, personality traits and behavioural patterns that influence judgement and decision-making.",
      "dimensions": [
        "Anchoring",
        "Confirmation bias",
        "Availability bias",
        "Halo effect",
        "Overconfidence",
        "Personality traits",
        "Personal resilience",
        "Emotional intelligence",
        "Conflict-resolution style",
        "Motivation",
        "Cognitive styles",
        "Adaptability",
        "Decision-making style",
        "Individual risk orientation, including cautious, risk-taking and adventure-seeking tendencies"
      ],
      "example": "An interviewer rates an introverted candidate as less capable of leadership, despite no evidence linking the two.",
      "note": "Boundary note: This category addresses cognitive mechanisms, psychological traits and individual tendencies. “Individual risk orientation” is distinct from Category 5’s organisational risk-management practices and institutional risk tolerance."
    },
    {
      "code": "D5",
      "title": "Category 5: Situational and Contextual Biases",
      "shortTitle": "Situational and Contextual Biases",
      "definition": "Bias arising from situational, organisational or environmental conditions that influence perceptions, evaluations and decision-making.",
      "dimensions": [
        "Power dynamics",
        "Role-based bias",
        "Organisational hierarchy",
        "Team dynamics",
        "Work environment",
        "Project assignments",
        "Resource availability",
        "Organisational culture",
        "Leadership influence",
        "Policy and procedure adherence",
        "Crisis situations",
        "Change management",
        "Innovation acceptance",
        "Organisational risk-management practices and institutional risk tolerance",
        "Cross-cultural interactions",
        "Situational stressors",
        "Organisational value alignment",
        "Environmental and sustainability value alignment",
        "Perceived organisational fit"
      ],
      "example": "Under severe time pressure during a system outage, a manager relies on a stereotype about a team rather than reviewing the complete evidence.",
      "note": "Boundary note: Organisational risk-management practices and institutional risk tolerance are contextual or organisational conditions. They are distinct from Category 4’s individual risk orientation."
    },
    {
      "code": "D6",
      "title": "Category 6: Technological and Media Biases",
      "shortTitle": "Technological and Media Biases",
      "definition": "Bias arising from technological systems, digital platforms and media environments that shape perceptions, evaluations and decision-making.",
      "dimensions": [
        "Digital literacy",
        "Technology access",
        "Technology adoption preferences",
        "Social media presence",
        "Online behaviour",
        "Digital footprint",
        "Media consumption habits",
        "Virtual communication styles",
        "Technological proficiency",
        "Preference for communication channels"
      ],
      "example": "A hiring manager interprets a limited online profile as evidence that an applicant lacks professional engagement.",
      "note": ""
    },
    {
      "code": "D7",
      "title": "Category 7: Cultural and Regional Biases",
      "shortTitle": "Cultural and Regional Biases",
      "definition": "Bias arising from cultural norms, traditions, regional identities and linguistic characteristics that influence perceptions, evaluations and decision-making.",
      "dimensions": [
        "Geographical location",
        "Cultural background",
        "Cultural norms and practices",
        "Regional dialects",
        "Voice accent",
        "Speech patterns",
        "Local customs",
        "Cultural heritage",
        "Traditions and celebrations",
        "Cultural adaptability",
        "Regional stereotypes",
        "Cultural expression styles",
        "Multicultural competence",
        "Cultural identity strength",
        "Generational cohort stereotypes (e.g., Generation Z, Millennials, Generation X or Baby Boomers)"
      ],
      "example": "A customer-service applicant is judged as less capable because of their regional accent.",
      "note": "Boundary note: “Generational cohort stereotypes” refers to culturally shared assumptions attached to a birth cohort as a social and cultural identity. This is distinct from “Age” in Category 1, which refers to chronological age as a demographic characteristic."
    },
    {
      "code": "D8",
      "title": "Category 8: Health and Wellness Biases",
      "shortTitle": "Health and Wellness Biases",
      "definition": "Bias arising from physical or mental health conditions, disability, neurodiversity, wellbeing or other health-related characteristics that influence perceptions, evaluations and treatment of individuals.",
      "dimensions": [
        "Physical health status",
        "Chronic illness",
        "Disability",
        "Neurodiversity",
        "Fitness assumptions",
        "Dietary and wellness practices where interpreted as health-related",
        "Health behaviours",
        "Healthcare access",
        "Body-image and weight-related health or wellbeing perceptions",
        "Mental health status"
      ],
      "example": "An employee with a disclosed long-term condition is passed over for promotion because of unsupported assumptions about reliability.",
      "note": "Boundary note: “Body-image and weight-related health or wellbeing perceptions” concerns an underlying health/wellbeing characteristic or perception. Category 9 captures observable appearance-based stereotyping, assumptions or differential treatment."
    },
    {
      "code": "D9",
      "title": "Category 9: Bias Manifestations and Indicators",
      "shortTitle": "Bias Manifestations and Indicators",
      "definition": "Observable expressions of underlying bias reflected in behaviour, communication, judgements and decision-making practices that reveal biased attitudes or preferences.",
      "dimensions": [
        "Differential rudeness or aggressiveness",
        "Stereotyping and generalisation",
        "Discriminatory or exclusionary language",
        "Microaggressions",
        "Favouritism",
        "Prejudicial statements or actions",
        "Unequal scrutiny",
        "Differential standards",
        "Social or organisational exclusion",
        "Appearance-based stereotyping, assumptions or differential treatment relating to physical appearance, height, weight, grooming, personal hygiene, fashion, personal style or body modification"
      ],
      "example": "Two equivalent candidates receive different levels of questioning and evidence requirements because of an identity-related assumption.",
      "note": "Structural note: Unlike Categories 1–8, this category represents manifestations rather than underlying sources. It captures observable evidence that an underlying bias has been expressed. Part F, Question 7 asks whether this should remain a category or be represented as a separate layer."
    },
    {
      "code": "D10",
      "title": "Intersectionality (Cross-Cutting Property)",
      "shortTitle": "Intersectionality",
      "definition": "A cross-cutting relational property capturing compounded effects across two or more source categories and, where relevant, between multiple attributes within a single source category, producing overlapping or non-linear forms of disadvantage or privilege.",
      "dimensions": [
        "Illustrative combinations: age × disability",
        "Gender × non-linear career path",
        "Neurodiversity × veteran status",
        "Socioeconomic status × digital footprint",
        "And gender × ethnicity (compounding within Personal Identity). These combinations use attributes already represented within Categories 1–8"
      ],
      "example": "An older employee with a disability is judged through the combined influence of age-related and disability-related assumptions in a way that cannot be adequately explained by either attribute independently.",
      "note": "Structural note: Intersectionality is not a standalone source or manifestation. It is a cross-cutting relational property outside the numbered sequence. It primarily captures compounded effects across different source categories while also allowing multiple attributes within one source category to compound."
    }
  ],
  "boundaryRows": [
    "Chronological age (Cat. 1) and generational cohort stereotypes (Cat. 7) are sufficiently distinguishable in practice.",
    "A social or alumni tie (Cat. 2) and institutional prestige used as a competence signal (Cat. 3) are sufficiently distinguishable.",
    "An individual’s own socioeconomic or marital status (Cat. 1) and relational constructs such as household composition (Cat. 2) are sufficiently distinguishable.",
    "Individual risk orientation (Cat. 4) and organisational risk practice or leadership influence (Cat. 5) are sufficiently distinguishable.",
    "A digital footprint (Cat. 6) and socioeconomic status (Cat. 1) are sufficiently distinguishable.",
    "Body-image or weight as a health/wellbeing perception (Cat. 8) and appearance-based differential treatment (Cat. 9) are sufficiently distinguishable.",
    "Where only differential treatment is observable, coding Category 9 alone without inferring a source category is workable."
  ],
  "wholeTaxonomyRows": [
    "The taxonomy has a clear and logical organising structure.",
    "The taxonomy covers the major sources and forms of bias relevant to human decision-making.",
    "The categories are collectively comprehensive.",
    "The categories are sufficiently distinct and unnecessary duplication is limited.",
    "The taxonomy is concise and avoids excessive complexity.",
    "The taxonomy is robust enough to represent different decision-making domains.",
    "The taxonomy can accommodate new or emerging bias dimensions.",
    "The taxonomy helps explain how bias may arise, interact or become observable.",
    "The distinction between underlying sources (Categories 1–8) and observable manifestations (Category 9) is conceptually clear.",
    "Intersectionality is appropriately represented as a cross-cutting relational property.",
    "A trained annotator could apply the taxonomy consistently to comparable narratives.",
    "The taxonomy is suitable for dataset development and annotation.",
    "The taxonomy is potentially useful for AI- or LLM-based bias detection.",
    "The terminology is appropriate for an interdisciplinary academic audience.",
    "The taxonomy offers a meaningful contribution beyond existing fragmented classifications."
  ],
  "openQuestions": [
    [
      "G_STRENGTHS",
      "What are the most important strengths of the proposed taxonomy?"
    ],
    [
      "G_WEAKNESSES",
      "What are the most important weaknesses or risks?"
    ],
    [
      "G_MISSING",
      "Are any important bias categories, dimensions, mechanisms or contexts missing? Please specify."
    ],
    [
      "G_MERGE",
      "Are any categories unnecessary, better merged, or better split?"
    ],
    [
      "G_HIERARCHY",
      "Are any dimensions located at the wrong level, or under the wrong parent category?"
    ],
    [
      "G_CAT9",
      "Should “Bias Manifestations and Indicators” remain Category 9, or be represented as a separate layer applied across all source categories?"
    ],
    [
      "G_CAT2",
      "Category 2 absorbs elective lifestyle and value-based dimensions (hobbies, pet ownership, travel preferences, personal values, philanthropic interests) that were previously a standalone “Lifestyle and Values Biases” category. Is this consolidation appropriate, or should they be separated again?"
    ],
    [
      "G_INTERSECTIONALITY",
      "Is intersectionality appropriately represented as a cross-cutting relational property rather than an additional category?"
    ],
    [
      "G_REFERENCES",
      "What theoretical perspectives or key references should be added? (optional)"
    ],
    [
      "G_ESSENTIAL",
      "What changes are essential before this taxonomy is used for dataset construction or AI-based bias detection?"
    ]
  ]
};

function buildExpertValidationForm() {
  const META = SPEC.meta;

  function fill(s) {
    return s
      .replace(/\{EMAIL\}/g, META.researcherEmail)
      .replace(/\{RETURN_BY\}/g, META.returnBy)
      .replace(/\{RETENTION\}/g, META.retentionPeriod);
  }

  const form = FormApp.create(SPEC.title);
  form.setDescription(fill(SPEC.description));

  // Google's newer Forms publishing model rejects some of these on some accounts
  // with "Invalid data updating form". None are essential to the instrument, so
  // a failure is logged rather than allowed to abort the build.
  function trySet(label, fn) {
    try {
      fn();
    } catch (e) {
      console.warn('Could not apply form setting "' + label + '": ' + e.message +
        '. Set it manually in the Forms UI if required.');
    }
  }

  trySet('progressBar', function () { form.setProgressBar(true); });
  trySet('shuffleQuestions', function () { form.setShuffleQuestions(false); });
  trySet('collectEmail', function () { form.setCollectEmail(false); });
  trySet('allowResponseEdits', function () { form.setAllowResponseEdits(false); });
  trySet('showLinkToRespondAgain', function () { form.setShowLinkToRespondAgain(false); });
  trySet('confirmationMessage', function () {
    form.setConfirmationMessage(
      'Thank you. Your expert assessment has been recorded.\n\n' +
      'If you wish to amend or withdraw your response, email ' + META.researcherEmail +
      ' quoting the reviewer code you entered at the start of this form.'
    );
  });
  // Must be set while the form is still open; the newer publishing model rejects
  // this call once responses have been switched off.
  trySet('customClosedFormMessage', function () {
    form.setCustomClosedFormMessage('This expert-validation form is still being finalised and is not yet accepting responses.');
  });
  trySet('acceptingResponses', function () { form.setAcceptingResponses(META.publish); });

  // -- Item helpers, each recording a codebook row --------------------------

  const codebook = [];
  function record(item, section, code, type, values, required, notes) {
    codebook.push([code, section, item.getTitle(), type, values, required ? 'Yes' : 'No', notes || '', item.getId()]);
    return item;
  }
  function addText(section, code, title, required, help) {
    const item = form.addTextItem().setTitle(code + ' — ' + title).setRequired(Boolean(required));
    if (help) item.setHelpText(help);
    return record(item, section, code, 'Short answer', 'Free text', required, help);
  }
  function addParagraph(section, code, title, required, help) {
    const item = form.addParagraphTextItem().setTitle(code + ' — ' + title).setRequired(Boolean(required));
    if (help) item.setHelpText(help);
    return record(item, section, code, 'Paragraph', 'Free text', required, help);
  }
  function addChoice(section, code, title, choices, required, help) {
    const item = form.addMultipleChoiceItem().setTitle(code + ' — ' + title).setChoiceValues(choices).setRequired(Boolean(required));
    if (help) item.setHelpText(help);
    return record(item, section, code, 'Multiple choice', choices.join(' | '), required, help);
  }
  function addCheckboxes(section, code, title, choices, required, help) {
    const item = form.addCheckboxItem().setTitle(code + ' — ' + title).setChoiceValues(choices).setRequired(Boolean(required));
    if (help) item.setHelpText(help);
    return record(item, section, code, 'Checkboxes', choices.join(' | '), required, help);
  }
  // Linear scale renders as one horizontal row of radio buttons with the anchor
  // wording at each end, rather than a vertical stack of long options.
  function addScale(section, code, title, low, high, lowLabel, highLabel, required, help) {
    const item = form.addScaleItem()
      .setTitle(code + ' — ' + title)
      .setBounds(low, high)
      .setLabels(lowLabel, highLabel)
      .setRequired(Boolean(required));
    if (help) item.setHelpText(help);
    return record(item, section, code, 'Linear scale',
      low + '–' + high + ' (' + low + ' = ' + lowLabel + ', ' + high + ' = ' + highLabel + ')',
      required, help);
  }
  function addGrid(section, code, title, rows, columns, required, help) {
    const item = form.addGridItem().setTitle(code + ' — ' + title).setRows(rows).setColumns(columns).setRequired(Boolean(required));
    if (help) item.setHelpText(help);
    rows.forEach(function (row, i) {
      codebook.push([
        code + '_R' + String(i + 1).padStart(2, '0'),
        section,
        item.getTitle() + ' [' + row + ']',
        'Multiple-choice grid row',
        columns.join(' | '),
        required ? 'Yes' : 'No',
        help || '',
        item.getId()
      ]);
    });
    return item;
  }

  // -- Part A: overview -----------------------------------------------------

  form.addSectionHeaderItem()
    .setTitle('Working definition of bias used in this study')
    .setHelpText(
      'Bias is a systematic deviation in human judgement or decision-making that is influenced by a ' +
      'characteristic, context, mechanism or signal not relevant to the objective merits of the ' +
      'decision, and which can favour or disadvantage particular individuals or groups.'
    );

  form.addSectionHeaderItem()
    .setTitle('Why this review is being carried out')
    .setHelpText(
      'Bias in decision-making is discussed across psychology, sociology, organisational studies, ' +
      'behavioural economics, information systems, healthcare, education and AI ethics, but the ' +
      'concepts are fragmented and the terminology inconsistent. This taxonomy brings them into one ' +
      'hierarchy while keeping meaningful conceptual boundaries. It was developed iteratively using ' +
      'Nickerson, Varshney and Muntermann (2013).\n\n' +
      'Your responses will refine category names and definitions, merge or relocate dimensions where ' +
      'justified, clarify boundaries between related categories, identify missing dimensions, and ' +
      'document the validation process in the research methodology.'
    );

  // -- Part B: consent and data protection ----------------------------------

  form.addPageBreakItem()
    .setTitle('Consent and data protection')
    .setHelpText(fill(SPEC.ethics.dataProtection));

  const declarations = form.addCheckboxItem()
    .setTitle('B_DECLARATIONS — Participation declaration')
    .setHelpText('All statements must be confirmed to proceed.')
    .setChoiceValues(SPEC.ethics.declarations)
    .setRequired(true);
  declarations.setValidation(
    FormApp.createCheckboxValidation().requireSelectAtLeast(SPEC.ethics.declarations.length).build()
  );
  record(declarations, 'Consent', 'B_DECLARATIONS', 'Checkboxes (all required)',
    SPEC.ethics.declarations.join(' | '), true,
    'Kept as separate confirmations rather than one combined statement, for the ethics audit trail.');

  const consent = form.addMultipleChoiceItem()
    .setTitle('B_CONSENT — Consent to participate')
    .setRequired(true);
  consent.setChoices([
    consent.createChoice('I consent to my responses being used for this research in accordance with the approved ethics arrangements.', FormApp.PageNavigationType.CONTINUE),
    consent.createChoice('I do not consent to participate.', FormApp.PageNavigationType.SUBMIT)
  ]);
  record(consent, 'Consent', 'B_CONSENT', 'Multiple choice with branching',
    'Consent | Do not consent', true,
    'Non-consenting respondents are routed straight to submit.');

  // -- Part C: expert profile -----------------------------------------------

  form.addPageBreakItem()
    .setTitle('About you')
    .setHelpText('Identifying fields are optional because identifiability and acknowledgement must follow the approved ethics arrangements. The reviewer code is required.');

  addText('Profile', 'B_REVIEWER_CODE', 'Reviewer code', true,
    'The code in your invitation email. This is how your response is identified for reminders, ' +
    'de-duplication and withdrawal requests. It is not linked to your name unless you choose to give it below.');
  addText('Profile', 'B_NAME', 'Full name (optional)', false);
  addText('Profile', 'B_JOB_TITLE', 'Job title (optional)', false);
  addText('Profile', 'B_ORGANISATION', 'Institution / organisation (optional)', false);
  addText('Profile', 'B_DISCIPLINE', 'Department / discipline', true);
  addParagraph('Profile', 'B_EXPERTISE', 'Primary area(s) of expertise relevant to bias in decision-making', true);
  addChoice('Profile', 'B_EXPERIENCE_YEARS', 'Years of relevant experience', SPEC.experienceBands, true,
    'Banded rather than free text so the variable is analysable without cleaning.');
  addParagraph('Profile', 'B_RELEVANT_WORK', 'Relevant publications, projects or roles (optional)', false);

  const emailItem = form.addTextItem()
    .setTitle('B_EMAIL — Email address (optional)')
    .setHelpText('Complete only if permitted by the approved ethics arrangements.')
    .setRequired(false);
  emailItem.setValidation(FormApp.createTextValidation().requireTextIsEmail().build());
  record(emailItem, 'Profile', 'B_EMAIL', 'Short answer (email-validated)', 'Valid email', false, '');

  addChoice('Profile', 'B_ACK_PERMISSION', 'May we acknowledge your name in the resulting publication?',
    ['Yes', 'No', 'To be confirmed'], true);

  // -- Part D: the taxonomy at a glance -------------------------------------
  //
  // Names and one-line focus only. Full definitions, dimensions, examples and
  // boundary notes live on each category's own page, so nothing is repeated and
  // no page carries a wall of text.

  form.addPageBreakItem()
    .setTitle('The proposed taxonomy at a glance')
    .setHelpText(
      'No questions on this page.\n\n' +
      'Categories 1–8 are underlying SOURCES of bias. Category 9 records observable MANIFESTATIONS. ' +
      'Intersectionality sits outside the numbered sequence as a cross-cutting relational property.\n\n' +
      'The full definition, dimensions, example and boundary notes for each category appear on that ' +
      'category’s own page, so you will not need to return here.'
    );

  form.addSectionHeaderItem()
    .setTitle('Categories 1–4 — sources')
    .setHelpText(
      '1  Personal Identity — intrinsic or socially recognised identity characteristics\n' +
      '2  Social and Relational — relationships, networks and perceived interpersonal similarity\n' +
      '3  Professional and Educational — roles, education, qualifications and career signals\n' +
      '4  Cognitive and Psychological — cognitive tendencies, traits and behavioural patterns'
    );
  form.addSectionHeaderItem()
    .setTitle('Categories 5–8 — sources')
    .setHelpText(
      '5  Situational and Contextual — situational, organisational and environmental conditions\n' +
      '6  Technological and Media — technological systems, digital platforms and media environments\n' +
      '7  Cultural and Regional — cultural norms, traditions, regional identity and language\n' +
      '8  Health and Wellness — health, disability, neurodiversity and wellbeing'
    );
  form.addSectionHeaderItem()
    .setTitle('Category 9 and Intersectionality — a different logical level')
    .setHelpText(
      '9  Bias Manifestations and Indicators — observable expressions of an underlying bias\n' +
      '   Intersectionality — compounded effects across two or more source categories, or between ' +
      'attributes within one source category'
    );

  form.addSectionHeaderItem()
    .setTitle('How the next section works')
    .setHelpText(
      'Each category is presented on its own page. The first question asks whether you wish to review ' +
      'it — answering "No" jumps straight to the next category, so categories outside your expertise ' +
      'cost you nothing. Most experts review two to four.\n\n' +
      'Within a category you choose to review, every rating row must be answered. Use N/A for a row ' +
      'that falls outside your expertise or cannot reasonably be assessed.'
    );

  // -- Part E: category pages, gated ----------------------------------------

  const pages = [];
  SPEC.categories.forEach(function (cat) {
    const section = cat.code + ' – ' + cat.shortTitle;

    const page = form.addPageBreakItem()
      .setTitle(cat.title)
      .setHelpText(
        'DEFINITION\n' + cat.definition + '\n\n' +
        'DIMENSIONS INCLUDED\n' + cat.dimensions.join('; ') + '.\n\n' +
        'ILLUSTRATIVE EXAMPLE\n' + cat.example +
        (cat.note ? '\n\n' + cat.note : '')
      );

    const gate = form.addMultipleChoiceItem()
      .setTitle(cat.code + '_REVIEW — ' + SPEC.gate.question)
      .setRequired(true);
    record(gate, section, cat.code + '_REVIEW', 'Multiple choice with branching',
      SPEC.gate.yes + ' | ' + SPEC.gate.no, true,
      'Skip logic. "No" navigates to the next category, so unreviewed categories are blank rather than partially filled.');

    addGrid(section, cat.code + '_RATINGS', 'How far do you agree with each statement?',
      SPEC.validationRows, SPEC.validationScale, true,
      'Use N/A only for a row that falls outside your expertise or cannot reasonably be assessed.');

    addChoice(section, cat.code + '_RELEVANCE',
      'How relevant is this category to the study of bias in human decision-making?',
      SPEC.relevanceOptions, true,
      'Four-point relevance scale with no neutral midpoint. This is the item the Content Validity ' +
      'Index is computed from; "Quite relevant" or "Highly relevant" counts as endorsement.');

    addCheckboxes(section, cat.code + '_MISPLACED',
      'Which listed dimensions, if any, do NOT belong in this category?',
      cat.dimensions.concat(['None — all listed dimensions belong here']), true,
      'Select every dimension you would move or remove. Structured rather than free text so the ' +
      'responses can be counted across the expert panel.');

    addCheckboxes(section, cat.code + '_OVERLAP',
      'Which other categories, if any, does this category overlap too strongly?',
      SPEC.categoryOptions.filter(function (o) { return o.indexOf(cat.shortTitle) === -1; })
        .concat(['No significant overlap']), true,
      'Aggregated across experts, these responses form a category-by-category overlap matrix.');

    addScale(section, cat.code + '_CONFIDENCE', 'How confident are you in the ratings you have just given?',
      1, 5, 'Very low', 'Very high', true,
      'Used as a sensitivity check on the content-validity index and to flag ratings given at the edge of an expert’s field.');

    addParagraph(section, cat.code + '_COMMENT',
      'Anything to add, remove, rename or relocate? Suggested wording is welcome. (optional)', false);

    pages.push({ page: page, gate: gate });
  });

  // -- Part F: boundaries ----------------------------------------------------

  const boundaryPage = form.addPageBreakItem()
    .setTitle('Boundaries between categories')
    .setHelpText(
      'Completed by everyone, including experts who reviewed only one or two categories in detail.\n\n' +
      'Each statement concerns a boundary the taxonomy currently marks as needing clarification. These ' +
      'are the points at which the claim that the categories are distinct is most likely to fail, so ' +
      'they are asked directly. Use N/A where a pair falls outside your expertise.'
    );

  // Wire the category gates now that every destination page exists.
  pages.forEach(function (entry, i) {
    const target = (i + 1 < pages.length) ? pages[i + 1].page : boundaryPage;
    entry.gate.setChoices([
      entry.gate.createChoice(SPEC.gate.yes, FormApp.PageNavigationType.CONTINUE),
      entry.gate.createChoice(SPEC.gate.no, target)
    ]);
  });

  addGrid('Boundaries', 'E_BOUNDARIES', 'How far do you agree with each statement?',
    SPEC.boundaryRows, SPEC.validationScale, true);
  addParagraph('Boundaries', 'E_BOUNDARY_COMMENT',
    'For any boundary you rated 1–3, how should the distinction be redrawn or the wording clarified? (optional)', false);

  // -- Part G: the taxonomy as a whole ---------------------------------------

  form.addPageBreakItem()
    .setTitle('The taxonomy as a whole')
    .setHelpText(
      'Completed by everyone.\n\n' +
      'As a reminder: 1 Personal Identity · 2 Social and Relational · 3 Professional and Educational · ' +
      '4 Cognitive and Psychological · 5 Situational and Contextual · 6 Technological and Media · ' +
      '7 Cultural and Regional · 8 Health and Wellness · 9 Bias Manifestations and Indicators · ' +
      'Intersectionality as a cross-cutting property.'
    );

  addGrid('Whole taxonomy', 'G_RATINGS', 'How far do you agree with each statement?',
    SPEC.wholeTaxonomyRows, SPEC.validationScale, true);
  addScale('Whole taxonomy', 'G_CONFIDENCE', 'How confident are you in your overall assessment?',
    1, 5, 'Very low', 'Very high', true);

  // -- Part H: recommendations and declaration -------------------------------

  form.addPageBreakItem()
    .setTitle('Your recommendations')
    .setHelpText('Please prioritise recommendations that would materially improve conceptual validity, practical usability, or readiness for dataset and AI applications. Every question here is optional.');

  SPEC.openQuestions.forEach(function (q) {
    addParagraph('Recommendations', q[0], q[1], false);
  });

  addChoice('Recommendation', 'G_OVERALL', 'Overall recommendation', [
    'Accept without changes',
    'Accept with minor revisions',
    'Accept with major revisions',
    'Further conceptual development is required before acceptance',
    'Unable to make an overall recommendation'
  ], true);

  const declaration = form.addCheckboxItem()
    .setTitle('G_DECLARATION — Final expert statement')
    .setChoiceValues(['I confirm that the ratings and comments in this form represent my independent expert assessment of the proposed taxonomy.'])
    .setRequired(true);
  record(declaration, 'Declaration', 'G_DECLARATION', 'Checkbox', 'Single required confirmation', true,
    'A drawn signature is not collected; add one only if the approved ethics arrangements require it.');

  addText('Declaration', 'G_EXPERT_NAME', 'Expert name for the declaration (optional)', false);
  const dateItem = form.addDateItem().setTitle('G_DATE — Date').setIncludesYear(true).setRequired(false);
  record(dateItem, 'Declaration', 'G_DATE', 'Date', 'Date', false,
    'Google Forms also records an automatic submission timestamp.');
  addParagraph('Declaration', 'G_ACK_WORDING', 'Preferred acknowledgement wording (optional)', false);

  // -- Response destination, README and data dictionary ----------------------

  const ss = SpreadsheetApp.create(SPEC.sheetTitle);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  const readme = ss.insertSheet('README');
  const readmeRows = [
    ['Expert Validation – Taxonomy Bias', 'Research data collection workbook'],
    ['Generated from', 'google_form_v2_spec.json via scripts/build_form_gs.py. Edit the spec, not the generated .gs.'],
    ['Status', META.publish ? 'LIVE — accepting responses.' : 'DRAFT — the linked form is not accepting responses.'],
    ['Instrument design', 'Expert-judgement instrument. One page per category, carrying that category\'s definition, dimensions and example. No scenario-annotation component: respondents are domain experts evaluating the taxonomy, not annotators applying it.'],
    ['Category review logic', 'Dn_REVIEW is the gate. "No" navigates to the next category, so a blank category block always means it was deliberately skipped. Within a reviewed category every question is required, so N/A is the only permitted non-answer. Skipped and missed are therefore distinguishable.'],
    ['CVI item', 'Dn_RELEVANCE uses a four-point relevance scale with no neutral midpoint (Lynn 1986; Polit & Beck). ENDORSEMENT RULE: "Quite relevant" or "Highly relevant" counts as endorsed. The five-point agreement grids retain a neutral midpoint and must not be used for CVI.'],
    ['CVI denominator rule', 'For each item, the denominator is the number of valid ratings actually given: exclude N/A, blanks, and categories skipped at the gate. I-CVI = endorsed / valid. S-CVI/Ave = mean of the I-CVIs. Report the denominator transparently for each item.'],
    ['Overlap matrix', 'Dn_OVERLAP asks which other categories this one overlaps. Tabulate as a 10x10 matrix of counts across the panel. Cells with high counts identify the pairs to merge or re-delimit, and should agree with the corresponding E_BOUNDARIES row. Disagreement between the two is itself worth reporting.'],
    ['Misplaced dimensions', 'Dn_MISPLACED lists that category\'s own dimensions as checkboxes. Count selections per dimension across the panel; any dimension selected by a substantial minority is a relocation candidate. This replaces the free-text "should any dimension be moved?" question, which in practice goes unanswered.'],
    ['Confidence weighting', 'Dn_CONFIDENCE is a 1-5 scale per reviewed category. Report the unweighted I-CVI as the primary figure and a confidence-weighted variant as a sensitivity check, not as a substitute.'],
    ['Boundary probe', 'E_BOUNDARIES names the specific pairs the taxonomy\'s boundary notes flag as contested. Any row with a median at or below 3, or wide dispersion, marks a boundary needing rewording before the taxonomy is used for annotation.'],
    ['Likert coding', '1 Strongly disagree; 2 Disagree; 3 Neither agree nor disagree; 4 Agree; 5 Strongly agree; N/A cannot assess.'],
    ['Identification', 'B_REVIEWER_CODE is a required pseudonymous key. It is the only reliable way to de-duplicate, send reminders and honour a withdrawal request. Name and email are optional.'],
    ['Scope limitation to state in the write-up', 'This instrument establishes content validity and conceptual quality. It does not establish that independent annotators apply the taxonomy consistently. If an inter-rater reliability claim is needed, run a separate annotation exercise over labelled decision narratives and report Fleiss\' kappa or Krippendorff\'s alpha from that.'],
    ['Before distribution', 'Replace ethics.dataProtection with approved ethics wording and the DPO contact; set meta.researcherEmail, meta.returnBy and meta.retentionPeriod; issue a unique reviewer code with each invitation; pilot with two reviewers; remove the DRAFT label from title and sheetTitle; set meta.publish to true; regenerate and re-run.'],
    ['Reference', 'Nickerson, R.C., Varshney, U. and Muntermann, J. (2013), European Journal of Information Systems, 22(3), 336–359. https://doi.org/10.1057/ejis.2012.26'],
    ['Edit URL', form.getEditUrl()],
    ['Responder URL', form.getPublishedUrl()]
  ];
  readme.getRange(1, 1, readmeRows.length, 2).setValues(readmeRows);
  readme.getRange('A1:B1').setFontWeight('bold').setBackground('#674ea7').setFontColor('#ffffff');
  readme.getRange('A2:A' + readmeRows.length).setFontWeight('bold');
  readme.setFrozenRows(1);
  readme.setColumnWidth(1, 200);
  readme.setColumnWidth(2, 760);
  readme.getDataRange().setWrap(true).setVerticalAlignment('top');

  const dict = ss.insertSheet('Data Dictionary');
  const headers = [['Variable code', 'Section', 'Question / exported field', 'Response type', 'Allowed values', 'Required', 'Notes', 'Form item ID']];
  dict.getRange(1, 1, 1, headers[0].length).setValues(headers);
  if (codebook.length) dict.getRange(2, 1, codebook.length, headers[0].length).setValues(codebook);
  dict.getRange(1, 1, 1, headers[0].length).setFontWeight('bold').setBackground('#674ea7').setFontColor('#ffffff');
  dict.setFrozenRows(1);
  dict.getDataRange().createFilter();
  dict.getDataRange().setWrap(true).setVerticalAlignment('top');
  [160, 240, 520, 190, 420, 90, 380, 120].forEach(function (w, i) { dict.setColumnWidth(i + 1, w); });

  const sheet1 = ss.getSheetByName('Sheet1');
  if (sheet1 && ss.getSheets().length > 1) ss.deleteSheet(sheet1);
  ss.setActiveSheet(readme);

  console.log(JSON.stringify({
    formId: form.getId(),
    editUrl: form.getEditUrl(),
    responderUrl: form.getPublishedUrl(),
    spreadsheetId: ss.getId(),
    spreadsheetUrl: ss.getUrl(),
    itemCount: form.getItems().length,
    codebookRows: codebook.length,
    acceptingResponses: form.isAcceptingResponses()
  }, null, 2));

  if (!META.publish && form.isAcceptingResponses()) {
    console.warn('ACTION REQUIRED: meta.publish is false but the form is still accepting responses. ' +
      'Open the form, go to the Responses tab and switch off "Accepting responses" before sharing the link.');
  }
}

function buildExpertValidationForm() {
  const FORM_TITLE = '[DRAFT – DO NOT DISTRIBUTE] Expert Validation: A Comprehensive Hierarchical Taxonomy of Biases in Human Decision-Making';
  const SHEET_TITLE = '[DRAFT] Expert Validation – Taxonomy Bias Responses';
  const SCALE_COLUMNS = [
    '1 — Strongly disagree',
    '2 — Disagree',
    '3 — Neither agree nor disagree',
    '4 — Agree',
    '5 — Strongly agree',
    'N/A — Outside expertise / cannot assess'
  ];
  const STANDARD_RATING_ROWS = [
    'The category name accurately represents its content.',
    'The definition is clear and understandable.',
    'The listed dimensions appropriately belong in this category.',
    'The category is relevant to the study of human decision-making bias.',
    'The category is sufficiently distinct from the other categories.',
    'The example accurately illustrates the category.',
    'The category can be applied across more than one decision-making domain.',
    'The category is useful for developing or annotating bias-detection datasets.'
  ];
  const STANDARD_COMMENTS = [
    ['ADD_REMOVE', 'What, if anything, should be added to or removed from this category?'],
    ['OVERLAP', 'Does this category overlap with another category? If yes, explain where and how the boundary should be clarified.'],
    ['RENAME', 'Would you rename this category or revise its definition? Please provide suggested wording.'],
    ['MOVE', 'Should any listed dimension be moved to another category?'],
    ['EXAMPLE', 'Please provide any additional example that would improve understanding.']
  ];

  const categories = [
    {
      code: 'D1',
      title: 'Category 1: Personal Identity Biases',
      definition: 'Bias arising from intrinsic or socially recognised personal identity characteristics that influence perceptions, evaluations and decision-making about individuals.',
      dimensions: 'Race; ethnicity; gender; age; religion; sexual orientation; national origin; socioeconomic status; language; marital status; parental status; veteran status; genetic information; legal status (e.g., citizenship, residency).',
      example: 'A hiring panel rates an equally qualified candidate lower after learning that they hold non-citizen status, despite the candidate having unrestricted permission to work.',
      note: 'Boundary note: “Socioeconomic Status” and “Marital Status”/“Parental Status” refer to an individual’s own demographic or social-position characteristics. Category 2 addresses related but distinct relational and behavioural constructs, including marital role expectations, parenting style, household composition and social-network affiliations.'
    },
    {
      code: 'D2',
      title: 'Category 2: Social and Relational Biases',
      definition: 'Bias arising from social relationships, interpersonal interactions, network affiliations and perceived similarity in interests or values that influence perceptions, evaluations and decision-making.',
      dimensions: 'Family responsibilities (e.g., caregiver roles); volunteer and community engagement; social networks; peer groups; affiliations; friendship circles; marital role expectations; parenting style; household composition (e.g., single-parent, extended family); shared hobbies and interests; pet ownership; travel and leisure preferences; personal values; philanthropic interests.',
      example: 'A manager gives a high-profile assignment to an employee from the same social network because they feel more comfortable with them.',
      note: 'Boundary note: This category concerns relational standing, social connection and perceived interpersonal similarity rather than demographic status itself. Elective lifestyle and value-based dimensions are included only where they function as signals of affinity or social compatibility. Part F, Question 8 asks directly whether this consolidation is appropriate.'
    },
    {
      code: 'D3',
      title: 'Category 3: Professional and Educational Biases',
      definition: 'Bias arising from professional roles, educational backgrounds, qualifications and career-related characteristics that influence perceptions of competence, credibility or suitability.',
      dimensions: 'Education; educational institution (e.g., alma mater prestige); field of study (e.g., STEM vs. humanities); work experience; professional title; certifications and licences; job title; industry (e.g., technology, finance, healthcare); career path (e.g., non-linear vs. linear); professional affiliations; employment history; professional skills; professional competencies.',
      example: 'A panel rates a candidate more highly mainly because they attended a prestigious university.',
      note: ''
    },
    {
      code: 'D4',
      title: 'Category 4: Cognitive and Psychological Biases',
      definition: 'Bias arising from psychological characteristics, cognitive tendencies, personality traits and behavioural patterns that influence judgement and decision-making.',
      dimensions: 'Anchoring; confirmation bias; availability bias; halo effect; overconfidence; personality traits; personal resilience; emotional intelligence; conflict-resolution style; motivation; cognitive styles; adaptability; decision-making style; individual risk orientation, including cautious, risk-taking and adventure-seeking tendencies.',
      example: 'An interviewer rates an introverted candidate as less capable of leadership, despite no evidence linking the two.',
      note: 'Boundary note: This category addresses cognitive mechanisms, psychological traits and individual tendencies. “Individual risk orientation” is distinct from Category 5’s organisational risk-management practices and institutional risk tolerance.'
    },
    {
      code: 'D5',
      title: 'Category 5: Situational and Contextual Biases',
      definition: 'Bias arising from situational, organisational or environmental conditions that influence perceptions, evaluations and decision-making.',
      dimensions: 'Power dynamics; role-based bias; organisational hierarchy; team dynamics; work environment; project assignments; resource availability; organisational culture; leadership influence; policy and procedure adherence; crisis situations; change management; innovation acceptance; organisational risk-management practices and institutional risk tolerance; cross-cultural interactions; situational stressors; organisational value alignment; environmental and sustainability value alignment; perceived organisational fit.',
      example: 'Under severe time pressure during a system outage, a manager relies on a stereotype about a team rather than reviewing the complete evidence.',
      note: 'Boundary note: Organisational risk-management practices and institutional risk tolerance are contextual or organisational conditions. They are distinct from Category 4’s individual risk orientation.'
    },
    {
      code: 'D6',
      title: 'Category 6: Technological and Media Biases',
      definition: 'Bias arising from technological systems, digital platforms and media environments that shape perceptions, evaluations and decision-making.',
      dimensions: 'Digital literacy; technology access; technology adoption preferences; social media presence; online behaviour; digital footprint; media consumption habits; virtual communication styles; technological proficiency; preference for communication channels.',
      example: 'A hiring manager interprets a limited online profile as evidence that an applicant lacks professional engagement.',
      note: ''
    },
    {
      code: 'D7',
      title: 'Category 7: Cultural and Regional Biases',
      definition: 'Bias arising from cultural norms, traditions, regional identities and linguistic characteristics that influence perceptions, evaluations and decision-making.',
      dimensions: 'Geographical location; cultural background; cultural norms and practices; regional dialects; voice accent; speech patterns; local customs; cultural heritage; traditions and celebrations; cultural adaptability; regional stereotypes; cultural expression styles; multicultural competence; cultural identity strength; generational cohort stereotypes (e.g., Generation Z, Millennials, Generation X or Baby Boomers).',
      example: 'A customer-service applicant is judged as less capable because of their regional accent.',
      note: 'Boundary note: “Generational cohort stereotypes” refers to culturally shared assumptions attached to a birth cohort as a social and cultural identity. This is distinct from “Age” in Category 1, which refers to chronological age as a demographic characteristic.'
    },
    {
      code: 'D8',
      title: 'Category 8: Health and Wellness Biases',
      definition: 'Bias arising from physical or mental health conditions, disability, neurodiversity, wellbeing or other health-related characteristics that influence perceptions, evaluations and treatment of individuals.',
      dimensions: 'Physical health status; chronic illness; disability; neurodiversity; fitness assumptions; dietary and wellness practices where interpreted as health-related; health behaviours; healthcare access; body-image and weight-related health or wellbeing perceptions; mental health status.',
      example: 'An employee with a disclosed long-term condition is passed over for promotion because of unsupported assumptions about reliability.',
      note: 'Boundary note: “Body-image and weight-related health or wellbeing perceptions” concerns an underlying health/wellbeing characteristic or perception. Category 9 captures observable appearance-based stereotyping, assumptions or differential treatment.'
    },
    {
      code: 'D9',
      title: 'Category 9: Bias Manifestations and Indicators',
      definition: 'Observable expressions of underlying bias reflected in behaviour, communication, judgements and decision-making practices that reveal biased attitudes or preferences.',
      dimensions: 'Differential rudeness or aggressiveness; stereotyping and generalisation; discriminatory or exclusionary language; microaggressions; favouritism; prejudicial statements or actions; unequal scrutiny; differential standards; social or organisational exclusion; appearance-based stereotyping, assumptions or differential treatment relating to physical appearance, height, weight, grooming, personal hygiene, fashion, personal style or body modification.',
      example: 'Two equivalent candidates receive different levels of questioning and evidence requirements because of an identity-related assumption.',
      note: 'Structural note: Unlike Categories 1–8, this category represents manifestations rather than underlying sources. It captures observable evidence that an underlying bias has been expressed. Part F, Question 7 asks whether this should remain a category or be represented as a separate layer.'
    },
    {
      code: 'D10',
      title: 'Intersectionality (Cross-Cutting Property)',
      definition: 'A cross-cutting relational property capturing compounded effects across two or more source categories and, where relevant, between multiple attributes within a single source category, producing overlapping or non-linear forms of disadvantage or privilege.',
      dimensions: 'Illustrative combinations: age × disability; gender × non-linear career path; neurodiversity × veteran status; socioeconomic status × digital footprint; and gender × ethnicity (compounding within Personal Identity). These combinations use attributes already represented within Categories 1–8.',
      example: 'An older employee with a disability is judged through the combined influence of age-related and disability-related assumptions in a way that cannot be adequately explained by either attribute independently.',
      note: 'Structural note: Intersectionality is not a standalone source or manifestation. It is a cross-cutting relational property outside the numbered sequence. It primarily captures compounded effects across different source categories while also allowing multiple attributes within one source category to compound.',
      ratingRows: [
        'The term “Intersectionality” accurately represents the proposed cross-cutting property.',
        'The definition is clear and understandable.',
        'The illustrative combinations appropriately demonstrate intersectional effects.',
        'Intersectionality is relevant to understanding human decision-making bias.',
        'Representing Intersectionality as a cross-cutting property rather than a standalone category is conceptually appropriate.',
        'The example accurately illustrates an intersectional effect.',
        'The cross-cutting property can be applied across different decision-making domains.',
        'The cross-cutting property is useful for developing or annotating bias-detection datasets.'
      ],
      comments: [
        ['ADD_REMOVE', 'What, if anything, should be added to or removed from the proposed treatment of Intersectionality?'],
        ['OVERLAP', 'Does the proposed treatment of Intersectionality conflict or overlap with any category boundaries? If yes, explain how it should be clarified.'],
        ['REVISE', 'Would you revise the term or definition of Intersectionality as used here? Please provide suggested wording.'],
        ['COMBINATIONS', 'Should any of the illustrative combinations be revised, removed or replaced?'],
        ['EXAMPLE', 'Please provide any additional intersectional example that would improve understanding.']
      ]
    }
  ];

  const wholeTaxonomyRows = [
    'The taxonomy has a clear and logical organising structure.',
    'The taxonomy covers the major sources and forms of bias relevant to human decision-making.',
    'The categories are collectively comprehensive.',
    'The categories are sufficiently distinct and unnecessary duplication is limited.',
    'The taxonomy is concise and avoids excessive complexity.',
    'The taxonomy is robust enough to represent different decision-making domains.',
    'The taxonomy can accommodate new or emerging bias dimensions.',
    'The taxonomy helps explain how bias may arise, interact or become observable.',
    'The taxonomy is suitable for supporting dataset development and annotation.',
    'The taxonomy is potentially useful for AI- or LLM-based bias detection.',
    'The terminology is appropriate for an interdisciplinary academic audience.',
    'The taxonomy offers a meaningful contribution beyond existing fragmented classifications.',
    'The distinction between Categories 1–8 as underlying sources and dimensions and Category 9 as observable manifestations and indicators is conceptually appropriate.',
    'Intersectionality is appropriately represented as a cross-cutting relational property rather than as an additional taxonomy category.'
  ];

  const directAssessment = [
    ['COMPREHENSIVENESS', 'Comprehensiveness: Are any important categories, dimensions, mechanisms or contexts missing?'],
    ['DISTINCTIVENESS', 'Mutual distinctiveness: Which categories or dimensions overlap too strongly?'],
    ['HIERARCHY', 'Hierarchy: Are dimensions located at the correct level and under the correct parent category?'],
    ['TERMINOLOGY', 'Terminology: Are any names too broad, too narrow, ambiguous or discipline-specific?'],
    ['BALANCE', 'Balance: Are some categories much more detailed than others without a clear reason?'],
    ['USABILITY', 'Practical usability: Could a trained annotator apply this taxonomy consistently to real decision narratives?'],
    ['COHERENCE', 'Theoretical coherence: Does the structure align with established theory in your field?'],
    ['FUTURE_USE', 'Future use: What revisions would make the taxonomy more useful for research, policy or AI applications?']
  ];

  const recommendations = [
    ['F1_STRENGTHS', '1. What are the three most important strengths of the proposed taxonomy?'],
    ['F2_WEAKNESSES', '2. What are the three most important weaknesses or risks?'],
    ['F3_MISSING', '3. Are any important bias categories or dimensions missing? Please specify.'],
    ['F4_MERGE', '4. Are any categories unnecessary or better merged?'],
    ['F5_RELOCATE', '5. Are there any dimensions that should be split, renamed or relocated?'],
    ['F6_SOURCE_MANIFESTATION', '6. Does the taxonomy adequately distinguish sources of bias from manifestations or indicators of bias?'],
    ['F7_CATEGORY9', '7. Is “Bias Manifestations and Indicators” (Category 9) conceptually appropriate, or should manifestations be represented as a separate layer across all categories?'],
    ['F8_CATEGORY2', '8. Category 2 incorporates elective lifestyle and value-based dimensions previously proposed as a standalone “Lifestyle and Values Biases” category. Is this consolidation appropriate, or should these dimensions form their own category?'],
    ['F9_INTERSECTIONALITY', '9. Is Intersectionality appropriately represented as a cross-cutting relational property? Does the treatment accommodate both cross-category interactions and compounding within a single source category?'],
    ['F10_REFERENCES', '10. What theoretical perspectives or key references should be added?'],
    ['F11_ESSENTIAL_CHANGES', '11. What changes are essential before the taxonomy is used for dataset construction or AI-based detection?']
  ];

  const form = FormApp.create(FORM_TITLE);
  form.setDescription(
    'Researcher: Saima Sammad | Doctoral research / PhD | University of Bradford\n' +
    'Supervisory team: Professor Hassan Ugail and Dr Kamran Mahroof\n\n' +
    'Purpose: Expert review of category clarity, relevance, distinctiveness, completeness and practical usefulness. ' +
    'Most experts will review 2–4 categories closely, plus the whole-taxonomy evaluation. Estimated time: 25–40 minutes; reviewing all categories may take 90–120 minutes.\n\n' +
    'DRAFT ACTIONS REQUIRED BEFORE DISTRIBUTION: insert the requested return date and contact email; replace the confidentiality placeholder with wording that exactly matches the approved ethics documentation; then remove the DRAFT label and enable responses.'
  );
  form.setProgressBar(true);
  form.setShuffleQuestions(false);
  form.setCollectEmail(false);
  form.setAllowResponseEdits(true);
  form.setShowLinkToRespondAgain(false);
  form.setConfirmationMessage('Thank you. Your expert assessment has been recorded. Please retain your response-edit link if you may wish to revise your answers.');
  form.setAcceptingResponses(false);
  form.setCustomClosedFormMessage('This expert-validation form is still being finalised and is not yet accepting responses.');

  const codebook = [];
  function recordItem(item, section, code, responseType, allowedValues, required, notes) {
    codebook.push([code, section, item.getTitle(), responseType, allowedValues, required ? 'Yes' : 'No', notes || '', item.getId()]);
    return item;
  }
  function addText(section, code, title, required, helpText) {
    const item = form.addTextItem().setTitle(code + ' — ' + title).setRequired(Boolean(required));
    if (helpText) item.setHelpText(helpText);
    return recordItem(item, section, code, 'Short answer', 'Free text', required, helpText || '');
  }
  function addParagraph(section, code, title, required, helpText) {
    const item = form.addParagraphTextItem().setTitle(code + ' — ' + title).setRequired(Boolean(required));
    if (helpText) item.setHelpText(helpText);
    return recordItem(item, section, code, 'Paragraph', 'Free text', required, helpText || '');
  }
  function addMultipleChoice(section, code, title, choices, required, helpText) {
    const item = form.addMultipleChoiceItem().setTitle(code + ' — ' + title).setChoiceValues(choices).setRequired(Boolean(required));
    if (helpText) item.setHelpText(helpText);
    return recordItem(item, section, code, 'Multiple choice', choices.join(' | '), required, helpText || '');
  }
  function addCheckboxes(section, code, title, choices, required, helpText) {
    const item = form.addCheckboxItem().setTitle(code + ' — ' + title).setChoiceValues(choices).setRequired(Boolean(required));
    if (helpText) item.setHelpText(helpText);
    return recordItem(item, section, code, 'Checkboxes', choices.join(' | '), required, helpText || '');
  }
  function addGrid(section, code, title, rows, required, helpText) {
    const item = form.addGridItem().setTitle(code + ' — ' + title).setRows(rows).setColumns(SCALE_COLUMNS).setRequired(Boolean(required));
    if (helpText) item.setHelpText(helpText);
    rows.forEach(function(row, index) {
      codebook.push([
        code + '_R' + String(index + 1).padStart(2, '0'),
        section,
        item.getTitle() + ' [' + row + ']',
        'Multiple-choice grid row',
        SCALE_COLUMNS.join(' | '),
        required ? 'Yes' : 'No',
        helpText || '',
        item.getId()
      ]);
    });
    return item;
  }

  // Part A/B: invitation, ethics placeholder and consent.
  form.addSectionHeaderItem()
    .setTitle('Part A. Invitation and study overview')
    .setHelpText(
      'The wider research aims to develop a theoretically grounded and practically usable taxonomy of human decision-making biases that can support systematic analysis, dataset development and AI/large-language-model-based detection of bias in decision narratives. Expert feedback may refine category names, definitions, dimensions, boundaries and examples.'
    );
  form.addSectionHeaderItem()
    .setTitle('Part B. Confidentiality and use of responses — ETHICS PLACEHOLDER')
    .setHelpText(
      'BEFORE DISTRIBUTION, replace this text with wording that exactly matches the approved ethics documentation, including whether experts will be named, anonymised or acknowledged only with explicit permission. The completed form will be used for academic research. Individual comments may be paraphrased or reported in aggregated form in accordance with the approved ethics arrangements.'
    );

  const consent = form.addMultipleChoiceItem()
    .setTitle('B_CONSENT — Participation declaration')
    .setHelpText('By choosing “I consent”, you confirm that you understand the purpose of this expert review; participation is voluntary; you understand how your feedback will be used; and you consent to its use in accordance with the approved ethics arrangements.')
    .setRequired(true);
  consent.setChoices([
    consent.createChoice('I understand the statements above and consent to participate.', FormApp.PageNavigationType.CONTINUE),
    consent.createChoice('I do not consent to participate.', FormApp.PageNavigationType.SUBMIT)
  ]);
  recordItem(consent, 'Part B – Consent', 'B_CONSENT', 'Multiple choice with branching', 'Consent | Do not consent', true, 'Non-consenting respondents are routed to submit without seeing the remaining sections.');

  // Expert profile and scope.
  form.addPageBreakItem().setTitle('Part B. Expert profile and scope of review').setHelpText('Profile fields are not marked required because identifiability and acknowledgement must follow the approved ethics arrangements. Select all categories you feel qualified to review.');
  addText('Part B – Expert profile', 'B_NAME', 'Full name', false);
  addText('Part B – Expert profile', 'B_JOB_TITLE', 'Job title', false);
  addText('Part B – Expert profile', 'B_ORGANISATION', 'Institution / organisation', false);
  addText('Part B – Expert profile', 'B_DISCIPLINE', 'Department / discipline', false);
  addParagraph('Part B – Expert profile', 'B_EXPERTISE', 'Primary area(s) of expertise', false);
  addText('Part B – Expert profile', 'B_EXPERIENCE_YEARS', 'Years of relevant experience', false, 'Enter a number or a brief range, for example “12” or “10–15”.');
  addParagraph('Part B – Expert profile', 'B_RELEVANT_WORK', 'Relevant publications, projects or roles (optional)', false);
  addText('Part B – Expert profile', 'B_EMAIL', 'Email address', false, 'Optional. Complete only if permitted by the approved ethics arrangements.');
  addMultipleChoice('Part B – Expert profile', 'B_ACK_PERMISSION', 'Permission to acknowledge your name in the publication', ['Yes', 'No', 'To be confirmed'], false);
  addCheckboxes(
    'Part B – Scope',
    'B_SCOPE',
    'Categories you feel qualified to review (select all that apply)',
    categories.map(function(category) { return category.title; }),
    false,
    'Most experts are expected to select 2–4 categories. You will still see every category section; leave unselected category grids and comments blank. Part E should be completed by all consenting participants.'
  );

  // Part C: overview and methodological basis.
  form.addPageBreakItem()
    .setTitle('Part C. Taxonomy overview and methodological basis')
    .setHelpText(
      'Working definition: Bias is a systematic deviation in human judgement or decision-making influenced by a characteristic, context, mechanism or signal not relevant to the objective merits of the decision, and which can favour or disadvantage particular individuals or groups.\n\n' +
      'The taxonomy was developed iteratively using Nickerson, Varshney and Muntermann (2013). Categories 1–8 represent underlying sources and dimensions; Category 9 captures observable manifestations and indicators; Intersectionality is represented outside the numbered sequence as a cross-cutting relational property.'
    );
  form.addSectionHeaderItem()
    .setTitle('Proposed high-level structure')
    .setHelpText(
      '1. Personal Identity — intrinsic or socially recognised identity characteristics.\n' +
      '2. Social and Relational — relationships, networks and perceived interpersonal similarity.\n' +
      '3. Professional and Educational — roles, education, qualifications and careers.\n' +
      '4. Cognitive and Psychological — cognitive tendencies, psychological traits and behavioural patterns.\n' +
      '5. Situational and Contextual — situational, organisational and environmental conditions.\n' +
      '6. Technological and Media — technological systems, digital platforms and media environments.\n' +
      '7. Cultural and Regional — cultural norms, traditions, regional identities and linguistic characteristics.\n' +
      '8. Health and Wellness — health, disability, neurodiversity and wellbeing.\n' +
      '9. Bias Manifestations and Indicators — observable expressions of underlying bias.\n' +
      'Intersectionality — compounded effects across categories or attributes within one source category.'
    );
  form.addSectionHeaderItem()
    .setTitle('Quality principles for this review')
    .setHelpText(
      'Clarity: understandable and unambiguous. Relevance: contributes meaningfully. Distinctiveness: clear boundaries and limited unnecessary overlap. Comprehensiveness: covers important forms, sources, contexts and manifestations. Conciseness: avoids duplication and excessive complexity. Robustness: represents varied real-world situations. Extendibility: incorporates new dimensions without disrupting the logic. Explanatory usefulness: helps explain how bias arises or becomes observable. Practical usefulness: guides annotation, analysis and AI-based detection.'
    );

  // Part D: category-by-category review.
  categories.forEach(function(category) {
    const help =
      'Proposed definition\n' + category.definition + '\n\n' +
      'Included dimensions / subcategories\n' + category.dimensions + '\n\n' +
      'Illustrative example\n' + category.example +
      (category.note ? '\n\n' + category.note : '');
    form.addPageBreakItem().setTitle('Part D. ' + category.title).setHelpText(help);
    addGrid(
      'Part D – ' + category.title,
      category.code + '_RATINGS',
      category.code === 'D10' ? 'Cross-cutting property evaluation' : 'Category evaluation',
      category.ratingRows || STANDARD_RATING_ROWS,
      false,
      'Complete this grid only if you selected this category in B_SCOPE. Use N/A only for an individual item that falls outside your expertise or cannot reasonably be assessed.'
    );
    (category.comments || STANDARD_COMMENTS).forEach(function(comment) {
      addParagraph('Part D – ' + category.title, category.code + '_' + comment[0], comment[1], false);
    });
  });

  // Part E: assessment of the taxonomy as a whole.
  form.addPageBreakItem().setTitle('Part E. Evaluation of the taxonomy as a whole').setHelpText('All consenting experts should complete this section. Select one response for every row; use N/A where an item cannot reasonably be assessed.');
  addGrid('Part E – Whole taxonomy', 'E_RATINGS', 'Whole-taxonomy evaluation', wholeTaxonomyRows, true, 'Required for all consenting participants.');
  form.addSectionHeaderItem().setTitle('Direct assessment of taxonomy quality').setHelpText('Please provide comments where you have relevant observations.');
  directAssessment.forEach(function(question) {
    addParagraph('Part E – Direct assessment', 'E_' + question[0], question[1], false);
  });

  // Part F: recommendations and final declaration.
  form.addPageBreakItem().setTitle('Part F. Open-ended recommendations and final declaration').setHelpText('Please prioritise recommendations that would materially improve conceptual validity, practical usability or readiness for dataset/AI applications.');
  recommendations.forEach(function(question) {
    addParagraph('Part F – Recommendations', question[0], question[1], false);
  });
  addMultipleChoice(
    'Part F – Overall recommendation',
    'F_OVERALL_RECOMMENDATION',
    'Overall recommendation',
    [
      'Accept without changes',
      'Accept with minor revisions',
      'Accept with major revisions',
      'Further conceptual development is required before acceptance',
      'Unable to make an overall recommendation'
    ],
    true
  );
  addCheckboxes(
    'Part F – Final declaration',
    'F_FINAL_CONFIRMATION',
    'Final expert statement',
    ['I confirm that the comments and ratings in this form represent my independent expert assessment of the proposed taxonomy.'],
    true
  );
  addText('Part F – Final declaration', 'F_EXPERT_NAME', 'Expert name for the final declaration', false, 'Optional unless the approved ethics arrangements require identification.');
  const dateItem = form.addDateItem().setTitle('F_DATE — Date').setIncludesYear(true).setRequired(false);
  recordItem(dateItem, 'Part F – Final declaration', 'F_DATE', 'Date', 'Date', false, 'Google Forms also records an automatic submission timestamp.');
  addParagraph('Part F – Final declaration', 'F_ACK_WORDING', 'Preferred acknowledgement wording (optional)', false);

  // Link a response spreadsheet and create an analysis-ready data dictionary.
  const spreadsheet = SpreadsheetApp.create(SHEET_TITLE);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, spreadsheet.getId());

  const readme = spreadsheet.insertSheet('README');
  const readmeRows = [
    ['Expert Validation – Taxonomy Bias', 'Research data collection workbook'],
    ['Status', 'DRAFT – the linked form is not accepting responses.'],
    ['Before distribution', 'Replace the ethics/confidentiality placeholder, add return date and contact email, remove the DRAFT label, verify settings, then enable responses.'],
    ['Likert coding', '1=Strongly disagree; 2=Disagree; 3=Neither agree nor disagree; 4=Agree; 5=Strongly agree; N/A=outside expertise/cannot assess.'],
    ['Category review logic', 'B_SCOPE records expertise. Part D grids are optional so unselected categories remain blank. N/A should be used only for individual items within a category being reviewed.'],
    ['CVI denominator rule', 'For each category-level or whole-taxonomy item, use the number of valid ratings actually provided. Exclude N/A and blanks, and report the denominator transparently.'],
    ['Signature', 'A required final confirmation is collected; a handwritten/drawn signature is not collected. Add one only if the approved ethics arrangements require it.'],
    ['Source reference', 'Nickerson, R.C., Varshney, U. and Muntermann, J. (2013), European Journal of Information Systems, 22(3), 336–359. https://doi.org/10.1057/ejis.2012.26'],
    ['Edit URL', form.getEditUrl()],
    ['Responder URL', form.getPublishedUrl()]
  ];
  readme.getRange(1, 1, readmeRows.length, 2).setValues(readmeRows);
  readme.getRange('A1:B1').setFontWeight('bold').setBackground('#674ea7').setFontColor('#ffffff');
  readme.getRange('A2:A' + readmeRows.length).setFontWeight('bold');
  readme.setFrozenRows(1);
  readme.setColumnWidth(1, 190);
  readme.setColumnWidth(2, 720);
  readme.getDataRange().setWrap(true).setVerticalAlignment('top');

  const dictionary = spreadsheet.insertSheet('Data Dictionary');
  const headers = [['Variable code', 'Section', 'Question / exported field', 'Response type', 'Allowed values', 'Required', 'Notes', 'Form item ID']];
  dictionary.getRange(1, 1, 1, headers[0].length).setValues(headers);
  if (codebook.length) dictionary.getRange(2, 1, codebook.length, headers[0].length).setValues(codebook);
  dictionary.getRange(1, 1, 1, headers[0].length).setFontWeight('bold').setBackground('#674ea7').setFontColor('#ffffff');
  dictionary.setFrozenRows(1);
  dictionary.getDataRange().createFilter();
  dictionary.getDataRange().setWrap(true).setVerticalAlignment('top');
  dictionary.setColumnWidth(1, 160);
  dictionary.setColumnWidth(2, 230);
  dictionary.setColumnWidth(3, 520);
  dictionary.setColumnWidth(4, 180);
  dictionary.setColumnWidth(5, 420);
  dictionary.setColumnWidth(6, 90);
  dictionary.setColumnWidth(7, 380);
  dictionary.setColumnWidth(8, 120);

  const defaultSheet = spreadsheet.getSheetByName('Sheet1');
  if (defaultSheet && spreadsheet.getSheets().length > 1) spreadsheet.deleteSheet(defaultSheet);
  spreadsheet.setActiveSheet(readme);

  console.log(JSON.stringify({
    formId: form.getId(),
    editUrl: form.getEditUrl(),
    responderUrl: form.getPublishedUrl(),
    spreadsheetId: spreadsheet.getId(),
    spreadsheetUrl: spreadsheet.getUrl(),
    itemCount: form.getItems().length,
    codebookRows: codebook.length,
    acceptingResponses: form.isAcceptingResponses()
  }, null, 2));
}

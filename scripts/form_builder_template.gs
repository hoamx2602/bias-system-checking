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

const SPEC = /*__SPEC__*/;

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

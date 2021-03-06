JsOsaDAS1.001.00bplist00�Vscript_
// Get the arXiv ID number from Safari
var safari = Application('Safari');
var matched_url = safari.windows[0].currentTab.url().match(/arxiv\.org.*\/([0-9.]+[^.])(\.pdf)?$/);

if (matched_url != null) {
	var arxiv_id = matched_url[1];
	var context = Application.currentApplication();
	context.includeStandardAdditions = true;

	// The Python script brings back a JSON object
	var script = Path(context.pathTo(this).toString() + '/Contents/Resources/Scripts/arxiv.py');
	var article = JSON.parse(context.doShellScript('/usr/local/miniconda3/bin/python3 "' + script + '" ' + arxiv_id));
	
	// Work with BibDesk to import the data
	var bd = Application('BibDesk');
	bd.includeStandardAdditions = true;
	var doc = bd.windows[0].document();
	
	// If a DOI is present, BibDesk brings it in. If not, we parse the API response in Python.
	if (article.doi != null) {
		var [paper] = doc.import({from: article.doi});	
	} else {
		var [paper] = doc.import({from: article.bibtex});	
	}

	// Add abstracts, linked URLs, downloaded PDFs (Python does this), and arXiv fields
	if (article.abstract != null) {
		paper.abstract = article.abstract;
	}
	for (i=0; i < article.links.length; i++) {
		bd.add(article.links[i], {to: paper.linkedURLs})
	}
	for (i=0; i < article.pdfs.length; i++) {
		bd.add(Path(article.pdfs[i]), {to: paper.linkedFiles})
	}
	
	paper.fields.byName("archivePrefix").value = "arXiv";
	paper.fields.byName("eprint").value = article.eprint.eprint;
	paper.fields.byName("primaryClass").value = article.eprint.primaryClass;
	
	// Open BibDesk
	bd.activate();
}
                              3 jscr  ��ޭ
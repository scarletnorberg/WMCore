// Set the dbname below to the same name you used when pushing the couchapp.
// This can only be determined during deployment time
dbname = "__fill_dbname_here__";

// Work around different mount points of couchdb
// so that it can run behind the frontend, with
// or without rewrites.
dbpath = document.location.href.split('/_design')[0];
dbpath = dbpath.split('/index.html')[0];
couchroot = dbpath.substring(0,dbpath.lastIndexOf('/'));

function couchapp_load(scripts) {
  for (var i=0; i < scripts.length; i++) {
    document.write('<script src="'+scripts[i]+'"><\/script>')
  };
};

couchapp_load([
   "vendor/couchapp/loader.js",
   "vendor/jquery/jquery-ui.min.js",
   "vendor/datatables/jquery.dataTables.min.js",
   "vendor/datatables/ColVis.min.js",
   "lib/namespace.js",
   "lib/jquery.dataTables.columnFilter.js"
]);
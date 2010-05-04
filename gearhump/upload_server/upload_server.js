var fs = require("fs"),
http = require("http"),
multipart = require("multipart"),
path = require("path"),
sys = require("sys"),
sha1 = require("./sha1"),
settings = require("./settings");

var gearhump_client = http.createClient(settings.gearhump_port,
  settings.gearhump_host);
var s3_client = http.createClient(settings.s3_port, settings.s3_host);

function log(msg) {
  process.stdio.writeError("LOG: " + new Date() + ": " + msg + "\n");
}

function debug(msg) {
  if (settings.debug)
    process.stdio.writeError("DEBUG: " + new Date() + ": " + msg + "\n");
}

function cleanupFile(file_path, cutoff) {
  fs.stat(file_path, function (err, stats) {
      if (err) {
        log("error cleaning cache: " + err);
        return;
      }
      var ctime = new Date(stats["ctime"]);
      if (ctime < cutoff) {
        debug("unlinking " + file_path);
        fs.unlink(file_path, function (err) {
            if (err)
              log("error unlinking file: " + err);
          });
      } 
    });
}

function cleanup() {
  fs.readdir(settings.cache_path, function (err, files) {
      if (err) {
        log("error cleaning cache: " + err);
        return;
      }
      var cutoff =
        new Date(new Date().getTime() - settings.cache_clean_interval_mins
          * 60 * 1000);
      for (i in files) {
        var file_path = path.join(settings.cache_path, files[i]);
        cleanupFile(file_path, cutoff);
      }
    });
}

setInterval(cleanup, settings.cache_clean_interval_mins * 60 * 1000);

function requestHandler(req, res) {
  var mp = multipart.parse(req);
  var gallery_id, upload_key;
  var files_started = 0;
  var files_finished = 0;
  var curr_path;
  var curr_file;
  var parse_finished = false;
  var active = true;
  var file_ids = {};
  var waiting_on_id = {};

  function cancel() {
    debug("canceling upload for gallery_id " + gallery_id);
    active = false;
    mp.removeAllListeners("error");
    mp.removeAllListeners("partBegin");
    mp.removeAllListeners("body");
    mp.removeAllListeners("partEnd");
    mp.removeAllListeners("complete");
    res.writeHead(302, {
        "Location": "http://" + settings.gearhump_host + ":"
        + settings.gearhump_port + "/g/" + gallery_id + "/upload_failure/"
      });
    res.close();
    if (curr_file) {
      curr_file.forceClose(function (err) {
          debug("error closing file: " + err);
        });
    }
  }

  function badRequest(msg) {
    cancel();
    log(msg);
  }

  function error(msg) {
    cancel();
    log(msg);
  }

  function getPhotoID(file_path) {
    debug("validating upload_key " + upload_key + " for gallery_id "
      + gallery_id);
    url = "/g/" + gallery_id + "/new_photo/" + upload_key; 
    var request = gearhump_client.request(url);
    request.addListener("response", function (response) {
        if (response.statusCode != 200) {
          error("error adding photo for gallery_id " + gallery_id);
        }
        else {
          var response_body = "";
          response.setBodyEncoding("utf8");
          response.addListener("data", function (chunk) {
              response_body += chunk;
            });
          response.addListener("end", function () {
              debug("got photo_id for " + file_path);
              file_ids[file_path] = JSON.parse(response_body)["photo_id"];
              if (waiting_on_id[file_path])
                upload_files(file_path);
            });
        }
      });
    request.close();
  }

  function partBegin(part) {
    if (part.name && part.name.indexOf("file") === 0) {
      if (gallery_id && upload_key) {
        var file_path = path.join(settings.cache_path, gallery_id + "_"
          + part.name.substring(4));
        debug("opening " + file_path);
        var file = fs.createWriteStream(file_path);
        file.addListener("error", function (err) {
            error(file_path + " " + err);
            file.forceClose(function (err) {
                debug("error closing file: " + err);
              });
          });
        curr_path = file_path;
        curr_file = file;
        files_started += 3;
        getPhotoID(file_path);
      }
      else {
        badRequest("got data before gallery_id and upload_key");
      }
    }
  }

  function body(chunk) {
    switch (mp.part.name) {
    case "gallery_id":
      debug("got gallery_id " + chunk);
      gallery_id = chunk;
      break;
    case "upload_key":
      debug("got upload_key " + chunk);
      upload_key = chunk;
      break;
    default:
      if (curr_file)
        curr_file.write(chunk);
      else
        badRequest("unknown part: " + mp.part.name);
    };
  }

  function partEnd(part) {
    if (part.name && part.name.indexOf("file") === 0 && curr_file) {
      debug("closing " + curr_path);
      var file_path = curr_path;
      curr_file.close(function (err) {
          if (err)
            error("failed to close " + file_path);
          else if (active)
            convert(file_path);
        });
      curr_file = undefined;
      curr_path = undefined;
    }
  }

  function convert(file_path) {
    debug("converting " + file_path);
    var new_path = file_path + ".jpg";
    sys.exec("convert " + file_path + " -quality 90 " + new_path,
      function (err, stdout, stderr) {
        if (err) {
          error("convert failed: " + err + ", " + stderr);
        }
        else if (active) {
          debug("successfully converted " + file_path);
          slide(file_path);
        }
      });
  }

  function slide(file_path) {
    debug("sliding " + file_path);
    sys.exec("convert " + file_path + " -resize '" + settings.max_slide_width
      + ">' -quality 90 " + file_path + "_s.jpg",
      function (err, stdout, stderr) {
        if (err) {
          error("slide failed: " + err + ", " + stderr);
        }
        else if (active) {
          debug("successfully slided " + file_path);
          thumbnail(file_path);
        }
      });
  }

  function thumbnail(file_path) {
    debug("thumbnailing " + file_path);
    sys.exec("convert " + file_path + " -thumbnail x"
      + (settings.thumb_width*2) + " -resize '" + (settings.thumb_width*2)
      + "<' -resize 50% -gravity center -crop " + settings.thumb_width + "x"
      + settings.thumb_width + "+0+0 +repage -quality 90 " + file_path
      + "_t.jpg",
      function (err, stdout, stderr) {
        if (err) {
          error("thumbnail failed: " + err + ", " + stderr);
        }
        else if (active) {
          debug("successfully thumbnailed " + file_path);
          if (file_path in file_ids)
            upload_files(file_path);
          else
            waiting_on_id[file_path] = true;
        }
      });
  }

  function sign(resource, dt, type, canon_amz_headers) {
    return sha1.b64_hmac_sha1(settings.s3_secret, "PUT\n\n" + type + "\n"
      + dt + "\n" + canon_amz_headers + "\n" + resource)
  }

  function canonicalize(arr) {
    var a = [], key, val;
    for (var i = 0; i < arr.length; i++){
      key = arr[i][0].toLowerCase();
      val = arr[i][1];
      a.push(key+':'+val)
    }
    return a.sort().join('\n')
  }

  function upload_files(orig_path) {
    var photo_id = file_ids[orig_path];
    upload(photo_id + ".jpg", orig_path + ".jpg");
    upload(photo_id + "_s.jpg", orig_path + "_s.jpg");
    upload(photo_id + "_t.jpg", orig_path + "_t.jpg");
  }

  function upload(s3_file_name, file_path) {
    debug("uploading " + file_path);
    fs.stat(file_path, function (err, stats) {
        if (err) {
          cancel("error stating " + file_path);
        }
        else {
          var length = stats.size;
          var type = "image/jpeg";
          var resource = "/" + settings.s3_bucket + "/" + settings.s3_prefix
          + s3_file_name;
          var amzheaders = [ ["x-amz-acl", "public-read"] ];
          var dt = new Date().toUTCString();
          var sig = sign(resource, dt, type, canonicalize(amzheaders));
          var headers = {
            "Date": dt,
            "Host": settings.s3_host,
            "User-Agent": "node.js",
            "Content-Length": length,
            "Content-Type": type,
            "Authorization": "AWS " + settings.s3_access + ":" + sig,
            "x-amz-acl": "public-read"
          }
          var request = s3_client.request("PUT", resource, headers);
          var rs = fs.createReadStream(file_path);
          rs.addListener("data", function (chunk) {
              request.write(chunk, "binary");
            });
          rs.addListener("end", function () {
              request.close();
            });
          rs.addListener("error", function (err) {
              error("error reading " + file_path + ", " + err);
              rs.forceClose(function (err) {
                  if (err)
                    debug("error closing " + file_path + ", " + err);
                });
            });
          request.addListener("response", function (response) {
              var response_body = "";
              response.setBodyEncoding("utf8");
              response.addListener("data", function (chunk) {
                  response_body += chunk;
                });
              response.addListener("end", function () {
                  debug(response_body);
                  if (response.statusCode != 200) {
                    error("error uploading " + s3_file_name);
                  }
                  else if (active) {
                    debug("successfully uploaded " + file_path);
                    files_finished++;
                    if (parse_finished && files_finished == files_started)
                      upload_finished();
                  }
                });
            });
        }
      });
  }

  function complete() {
    debug("parse finished for gallery_id " + gallery_id);
    parse_finished = true;
    if (files_finished == files_started)
      upload_finished();
  }

  function upload_finished() {
    debug("upload finished for gallery_id " + gallery_id);
    res.writeHead(302, {
        "Location": "http://" + settings.gearhump_host + ":"
        + settings.gearhump_port + "/g/" + gallery_id + "/upload_success/"
      });
    res.close();
  }

  mp.addListener("error", error);
  mp.addListener("partBegin", partBegin);
  mp.addListener("body", body); 
  mp.addListener("partEnd", partEnd);
  mp.addListener("complete", complete);
}

http.createServer(requestHandler).listen(settings.port);

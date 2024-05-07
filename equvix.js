var centicles = {
  map: false,
  grat: false,
  gratll: false,
  ctrll: false,
  cents: new Array(100),

  sign_add: function (x, y) {
    return x + (y * (x > 0 ? 1 : -1));
  },
  sign_addLL: function (latlng, tP, gP) {
    var t = latlng.lat(), g = latlng.lng();
    return new google.maps.LatLng(centicles.sign_add(t, tP), 
                                  centicles.sign_add(g, gP));
  },
  makeSqrCoords: function (latlng, size) {
    var other = centicles.sign_addLL(latlng, size, size),
        gtZero = latlng.lng() > 0;
    var first = (gtZero ? latlng : other),
        second = (gtZero ? other : latlng);
    var b = new google.maps.LatLngBounds(first, second);
    //console.debug(b.toUrlValue(3));
    return b;
  },
  makeGratCoords:function() {
    return centicles.makeSqrCoords(centicles.gratll, 1);
  },
  makeGrat: function () {
    var sqr = new google.maps.Rectangle({
      map: centicles.map,
      bounds: centicles.makeGratCoords(),
      strokeColor: "#0000FF",
      strokeOpacity: 0.8,
      strokeWeight: 1,
      fillOpacity: 0.0
    });
    return sqr;
  },
  
  makeCentCoords: function(cent) {
    var tc = Math.floor(cent / 10) / 10,
        gc = (cent % 10) / 10;
    return centicles.makeSqrCoords(
      centicles.sign_addLL(centicles.gratll,tc,gc),0.1);
  },
  makeCent: function (cent) {
    //console.debug(cent,latlngC.toUrlValue(2));
    var sqr = new google.maps.Rectangle({
      map: centicles.map,
      bounds: centicles.makeCentCoords(cent),
      strokeColor: "#FF0000",
      strokeOpacity: 0.8,
      strokeWeight: 0.5,
      fillColor: "#FF0000",
      fillOpacity: 0.10
    });
    return sqr;
  },

  LatLng2cent: function (latlng) {
    function tenths(x) { return Math.floor((Math.abs(x) * 10) % 10); }

    console.debug(tenths(latlng.lat()) + ":" + tenths(latlng.lng()));
    return (tenths(latlng.lat()) * 10) + tenths(latlng.lng());
  },

  qs: function() {
    //Copied from http://stackoverflow.com/a/10049330/450246
    var queryString = window.location.search || '';
    var keyValPairs = [];
    var params = {};
    queryString = queryString.substr(1);

    if (queryString.length) {
      keyValPairs = queryString.split('&');
      for (var pairNum in keyValPairs) {
        var key = keyValPairs[pairNum].split('=')[0];
        if (!key.length) continue;
        if (typeof params[key] === 'undefined') params[key] = [];
        params[key].push(keyValPairs[pairNum].split('=')[1]);
      }
    }
    //End copy
    return params;
  },    
  setLatLng: function(latlng) {
    centicles.gratll = new google.maps.LatLng(latlng.lat() | 0, latlng.lng() | 0);
    centicles.ctrll = centicles.sign_addLL(centicles.gratll, 0.5, 0.5);
  },

  initialize: function () {
    var params=centicles.qs();
    centicles.setLatLng(new google.maps.LatLng(params.lat, params.lng));
    
    centicles.map = new google.maps.Map(document.getElementById('map_canvas'), {
      zoom: 8,
      center: centicles.ctrll,
      mapTypeId: google.maps.MapTypeId.ROADMAP
    });
  
    centicles.grat = centicles.makeGrat();
    google.maps.event.addListener(centicles.map, 'click', centicles.gratClick);
    for (var cent = 0; cent < 100; cent++) {
      centicles.cents[cent] = centicles.makeCent(cent);
      google.maps.event.addListener(centicles.cents[cent], 'click', centicles.centClick);
    }
  },

  centClick: function (evt) {
    //console.debug("event: " + evt.latLng);
    centicles.cents[centicles.LatLng2cent(evt.latLng)].toggle();
    centicles.listActives();
  },
  
  listActives: function () {
    var actives = centicles.cents.map(function (v, i) {
      return v.active ? i : -1;
    }).filter(function (x) {
      return x != -1;
    }).join(' ');
    document.getElementById("active_cents").innerHTML = actives;
  },
  
  gratClick: function(evt) {
    centicles.setLatLng(evt.latLng);
    
    centicles.map.panTo(centicles.ctrll);
    document.getElementById("lat").innerHTML = centicles.gratll.lat();
    document.getElementById("lng").innerHTML = centicles.gratll.lng();

    centicles.grat.setBounds(centicles.makeGratCoords());
    for (var cent = 0; cent < 100; cent++) {
      centicles.cents[cent].setBounds(centicles.makeCentCoords(cent));
    }
  }
};

google.maps.Rectangle.prototype.toggle = function () {
  this.active = !this.active;
  this.setOptions({
    fillOpacity: (this.active ? 0.40 : 0.1)
  });
};

google.maps.event.addDomListener(window, 'load', centicles.initialize);  

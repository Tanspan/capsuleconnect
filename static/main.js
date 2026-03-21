// CapsuleConnect — main.js
$(function(){

  // Form validation
  $('#regForm').submit(function(e){
    var ok=true;
    var un=$('#un').val().trim(), em=$('#em').val().trim(), pw=$('#pw').val();
    if(un.length<3){ err('#un','Min 3 chars'); ok=false; } else ok('#un');
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)){ err('#em','Invalid email'); ok=false; } else ok('#em');
    if(pw.length<6){ err('#pw','Min 6 chars'); ok=false; }
    else if(!/\d/.test(pw)){ err('#pw','Need a number'); ok=false; } else ok('#pw');
    if(!ok) e.preventDefault();
  });

  $('#loginForm').submit(function(e){
    var ok=true;
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test($('#lem').val().trim())){ err('#lem','Invalid email'); ok=false; } else ok('#lem');
    if(!$('#lpw').val().trim()){ err('#lpw','Required'); ok=false; } else ok('#lpw');
    if(!ok) e.preventDefault();
  });

  $('#createForm').submit(function(e){
    var ok=true;
    if(!$('#ctitle').val().trim()){ err('#ctitle','Required'); ok=false; } else ok('#ctitle');
    if($('#cmsg').val().trim().length<10){ err('#cmsg','Min 10 chars'); ok=false; } else ok('#cmsg');
    var d=$('#cdate').val();
    if(!d){ err('#cdate','Required'); ok=false; }
    else if(new Date(d)<=new Date()){ err('#cdate','Must be future'); ok=false; } else ok('#cdate');
    if(!ok) e.preventDefault();
  });

  function err(s,m){ $(s).addClass('is-invalid').removeClass('is-valid').next('.invalid-feedback').remove(); $(s).after('<div class="invalid-feedback">'+m+'</div>'); }
  function ok(s){ $(s).removeClass('is-invalid').addClass('is-valid').next('.invalid-feedback').remove(); }

  // Set datetime min
  var dt=$('input[name="unlock_date"]');
  if(dt.length){ var n=new Date(); n.setMinutes(n.getMinutes()-n.getTimezoneOffset()); dt.attr('min',n.toISOString().slice(0,16)); }

  // Dashboard tabs
  $(document).on('click','.tab-btn',function(){
    var t=$(this).data('t');
    $('.tab-btn').removeClass('active');
    $(this).addClass('active');
    $('.tab-pane').hide();
    $('#t-'+t).fadeIn(200);
  });

  // Filter pills
  $(document).on('click','.filter-pill',function(){
    var cat=$(this).data('cat');
    $('.filter-pill').removeClass('active');
    $(this).addClass('active');
    $('.cap-col').each(function(){ $(this).toggle(cat==='all'||$(this).data('cat')===cat); });
  });

  // Capsule autocomplete
  var acT;
  $('#recip').on('input',function(){
    clearTimeout(acT);
    var q=$(this).val().trim();
    if(q.length<2){ $('#acbox').hide(); return; }
    acT=setTimeout(function(){
      $.getJSON('/search_users',{q:q},function(r){
        if(!r.length){ $('#acbox').hide(); return; }
        $('#acbox').html(r.map(function(u){ return '<div class="ac-item" data-u="'+u+'">@'+u+'</div>'; }).join('')).show();
      });
    },300);
  });
  $(document).on('click','.ac-item',function(){ $('#recip').val($(this).data('u')); $('#acbox').hide(); });
  $(document).click(function(e){ if(!$(e.target).closest('#recipWrap').length) $('#acbox').hide(); });

  // Countdowns
  function cd(){
    $('[data-unlock]').each(function(){
      var diff=new Date($(this).data('unlock'))-new Date();
      if(diff<=0){ $(this).text('Unlocking…'); return; }
      var d=Math.floor(diff/86400000),h=Math.floor(diff%86400000/3600000),m=Math.floor(diff%3600000/60000),s=Math.floor(diff%60000/1000);
      $(this).text($(this).hasClass('bigcd')?(d>0?d+'d '+h+'h '+m+'m '+s+'s':h+'h '+m+'m '+s+'s'):(d>0?d+'d '+h+'h left':h>0?h+'h '+m+'m left':m+'m left'));
    });
  }
  cd(); setInterval(cd,1000);

  // Chat textarea resize + enter
  $('#minput').on('input',function(){ this.style.height='auto'; this.style.height=Math.min(this.scrollHeight,110)+'px'; });
  $('#minput').keydown(function(e){ if(e.key==='Enter'&&!e.shiftKey){ e.preventDefault(); doSend(); } });
  $('#sbtn').click(doSend);

  // Schedule toggle
  $('#scbtn').click(function(){
    $(this).toggleClass('on');
    $('#scpick').slideToggle(150);
    if(!$(this).hasClass('on')) $('#scin').val('');
  });

  // Image pick
  $('#imgbtn').click(function(){ $('#fimg').click(); });
  $('#fimg').change(function(){
    if(!this.files[0]) return;
    window._imgFile=this.files[0];
    var r=new FileReader();
    r.onload=function(e){ $('#ithumb').attr('src',e.target.result); $('#iprev').slideDown(150); };
    r.readAsDataURL(this.files[0]);
  });
  $('#rimg').click(function(){ window._imgFile=null; $('#fimg').val(''); $('#iprev').slideUp(150); });

  // Scroll chat to bottom
  var ma=$('#marea'); if(ma.length) ma.scrollTop(ma[0].scrollHeight);

  // Schedule input min
  var si=document.getElementById('scin');
  if(si){ var n=new Date(); n.setMinutes(n.getMinutes()-n.getTimezoneOffset()+1); si.min=n.toISOString().slice(0,16); }

  // Break reminder
  var bt,bi;
  function startBt(){ clearTimeout(bt); bt=setTimeout(showB,20*60*1000); }
  function showB(){
    $('#bmodal').addClass('on'); var s=20;
    bi=setInterval(function(){ s--; $('#bsecs').text(s); $('#bcd').text('0:'+('0'+s).slice(-2)); if(s<=0){ clearInterval(bi); dismissB(); } },1000);
  }
  window.dismissB=function(){ $('#bmodal').removeClass('on'); clearInterval(bi); startBt(); };
  $(document).on('mousemove keydown click scroll',startBt);
  startBt();

  // Lightbox
  window.openLB=function(src){ $('#lbimg').attr('src',src); $('#lbox').addClass('on'); };
  $('#lbox').click(function(){ $(this).removeClass('on'); });

});

// Send chat message
function doSend(){
  var oid=window.OID; if(!oid) return;
  var txt=$('#minput').val().trim();
  var sat=$('#scbtn').hasClass('on')&&$('#scin').val()?$('#scin').val():null;
  if(!txt&&!window._imgFile) return;
  $('#minput').val('').css('height','auto');
  var fd=new FormData();
  fd.append('receiver_id',oid); fd.append('content',txt||'');
  if(sat) fd.append('scheduled_at',sat);
  if(window._imgFile) fd.append('image',window._imgFile);
  $.ajax({ url:'/send', method:'POST', data:fd, processData:false, contentType:false,
    success:function(d){
      if(!d.ok) return;
      if(d.sched){
        addMsg(txt,d.time,'',true);
        toast('Scheduled for '+new Date(sat).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}));
        if($('#scbtn').hasClass('on')) $('#scbtn').click();
      } else { addMsg(txt,d.time,d.img,false); }
      window._imgFile=null; $('#fimg').val(''); $('#iprev').slideUp(150);
    }
  });
}

function addMsg(txt,time,img,isPend){
  var bc=isPend?'bubble pending':'bubble';
  var tl=isPend?time+' <span style="font-size:.62rem;color:var(--gold);margin-left:3px;">scheduled</span>':time;
  var html='<div><div class="tlbl r">'+tl+'</div><div class="msg-row mine"><div>'+(img?'<img src="'+img+'" style="max-width:200px;border-radius:8px;display:block;cursor:pointer;" onclick="openLB(this.src)">':'')+(txt?'<div class="'+bc+'">'+esc(txt)+'</div>':'')+'</div></div></div>';
  var ma=$('#marea'); ma.append(html).scrollTop(ma[0].scrollHeight);
}

function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function toast(m){
  var t=$('<div style="position:fixed;bottom:75px;left:50%;transform:translateX(-50%);background:#141416;border:1px solid var(--gold);border-radius:9px;padding:10px 20px;font-size:.8rem;z-index:9999;white-space:nowrap;">'+m+'</div>');
  $('body').append(t); setTimeout(function(){ t.fadeOut(300,function(){ t.remove(); }); },3000);
}

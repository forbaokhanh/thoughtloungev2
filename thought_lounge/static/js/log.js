"use strict";

$(document).ready(function() {
    loadLogLounges();
});

function getLogLoungeData(lounge) {
    var logLoungeData = JSON.parse(JSON.stringify(lounge));
    
    
    logLoungeData.dateTime = formatDate(lounge.dateTime);
    //loungeData.topic
    return logLoungeData;
}

function loadLogLoungesError() {
    $('#logLoungeError').html(error('We couldn\'t load the Lounge Log. Please refresh the page to try again.'));
    return;
}

function loadLogLounges () {
    var logLoungesPromise = getLounges({time: 'past'})

    logLoungesPromise = logLoungesPromise.then(function(lounges, textStatus, jqXHR) {
        var logLoungesDataPromise = lounges.items.map(function(lounge) {
            return getLogLoungeData(lounge);
        });
        return $.when.apply($, logLoungesDataPromise).then(function(){
            return {
                'items': getArguments(arguments)
            };
        });
    });

    logLoungesPromise.done(function(logLounges) {
        var template = $('#logLoungesTemplate').html();
        var rendered = Mustache.render(template, logLounges);
        $('#logLounges').html(rendered);

        // getElementById because jQuery can't look for ids with /s
        var selectedLog = document.getElementById(logLoungeHref);
        if (!selectedLog)
            selectedLog = $('#logLounges').children()[0]
        $(selectedLog).click()
    }).fail(function(error, textStatus, jqXHR){
        loadLogLoungesError();
    });
}

function getLogLoungeInfoData(lounge) {
    return $.when(loungeToLoungeUsers(lounge, {type: 'showed-up', expand: 'user'}), loungeToHost(lounge)).then(function(loungeUsersData, loungeHostData) {
        var loungeUsers = loungeUsersData[0]
        var host = loungeHostData[0]

        var loungeData = JSON.parse(JSON.stringify(lounge));
        loungeData.dateTime = formatDate(lounge.dateTime);
        //loungeData.summary == lounge.summary

        //loungeData.topic == lounge.topic --- the quote inserted in the very beginning --- common name for a lounge
        //loungeData.host.firstName
        loungeData.host = host;
        
        loungeUsers.items.map(function(loungeUser) {
            loungeUser.summary = loungeUser.summary.split('\n');
            return loungeUser;
        });
        
        loungeData.loungeUsers = loungeUsers;

        return loungeToPictures(lounge).then(function(pictures, textStatus, jqXHR) {
            loungeData.pictures = pictures;
            return loungeData
        })
        // console.log(loungeUserDataPromises)
        // return $.when.apply($, loungeUserDataPromises).done( function(rValue) { console.log("TEST"); console.log(rValue) } ).returnJSON;
    });
}

$('#logLounges').on('click', '.logLounge', function(event) {
    event.preventDefault();

    $('.logLounge').each(function() {
        $(this).removeClass('active');
    })    
    $(event.target).closest('a').addClass('active');

    var logLoungeHref = $(event.target).closest('a').prop('id');
    var logLoungePromise = $.ajax({
        type: 'GET',
        url: logLoungeHref
    });
    var logLoungeInfoDataPromise = logLoungePromise.then( function(logLounge, textStatus, jqXHR) {
        return getLogLoungeInfoData(logLounge);
    })
     
    logLoungeInfoDataPromise.done(function(logLoungeInfoData) {
        var template = $('#logLoungeInfoTemplate').html();
        // console.log(logLoungeInfoData);
        var rendered = Mustache.render(template, logLoungeInfoData);
        $('#logLoungeInfo').html(rendered);
    }).fail(function(error, textStatus, jqXHR){
        loadLogLoungesError();
    });
})

/*$('#prevLounges').on('click', '.prevLounge', function(event) {
    event.preventDefault();

    var template = $('#loungeSumTemplate').html();
    var rendered = Mustache.render(template, lounge);
    $('#loungeSum').html(rendered);
}*/

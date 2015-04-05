"use strict";

$(document).ready(function() {
    loadWelcomeMessage();
    loadBio();
    loadPicture();
    loadUpcomingUserLounges();
    loadUserLounges();
});

// if someone is previewing a host's page, loads that. otherwise, their own info.
function loadUserOrPreview() {
    function loadHostError() {
        $('#welcomeMessage').html(error('We couldn\'t load this host\'s page. Please refresh the page to try again.'));
        return;
    }
    if (!hostHref) {
        return loadUser();
    } else {
        return globals.hostToPreview;
    }
}

function loadWelcomeMessage() {
    var user = loadUserOrPreview();
    var template = $('#welcomeMessageTemplate').html();
    var rendered = Mustache.render(template, user);
    $('#welcomeMessage').html(rendered);
}

function loadBio() {
    console.log('loading bio');
    var user = loadUserOrPreview();
    user.originalBio = user.bio;
    console.log(user.originalBio);
    user.bio = user.originalBio.split('\n');
    var template = $('#bioTemplate').html();
    var rendered = Mustache.render(template, user);
    $('#bio').html(rendered);
    user.bio = user.originalBio;
}

function loadPicture() {
    var user = loadUserOrPreview();

    function loadPictureError() {
        $('#welcomeMessage').html(error('We couldn\'t load your picture. Please refresh the page to try again.'));
        return;
    }
    
    // Hide when reload picture after submitting picture
    if (!user.picture.href) {
        var template = $('#upload-picture-template').html()
        var rendered = Mustache.render(template)
        $('#upload-picture').html(rendered);
        $('#upload-picture').show();
        $('#picture').hide();
        $('#delete-picture').hide();
        return;
    }
    else {
        $('#upload-picture').hide();
        $('#picture').show();
        $('#delete-picture').show();
    }

    $.ajax({
        type: 'GET',
        url: user.picture.href 
    }).done(function(picture, textStatus, jqXHR) {
        var template = $('#picture-template').html();
        var rendered = Mustache.render(template, picture);
        $('#picture').html(rendered);
        var template = $('#delete-picture-template').html();
        var rendered = Mustache.render(template);
        $('#delete-picture').html(rendered);
    }).fail(function(picture, textStatus, jqXHR) {
        loadPictureError();
    });
}

function loadUserLounges() {
    var user = loadUserOrPreview();
    function loadUserLoungesError() {
        $('#welcomeMessage').html(error('We couldn\'t load your lounges. Please refresh the page to try again.'));
        return;
    }

    $.ajax({
        type: 'GET',
        url: user.userLounges.href,
        data: 'time=past' 
    }).done(function(userLounges, textStatus, jqXHR) {
        var userLoungeCalls = [];
       
        $.each(userLounges.items, function(index, userLounge) {
            // Populating the host attribute with the actual user info 
            userLoungeCalls.push(
                $.ajax({
                    type: 'GET',
                    url: userLounge.lounge.href
                }).done(function(lounge, textStatus, jqXHR) {
                    userLounge.lounge = lounge;
                    userLounge.lounge.dateTime = formatDate(userLounge.lounge.dateTime); 
                }).fail(function(lounge, textStatus, jqXHR) {
                    loadUserLoungesError();
                })
            );
        });
        
        $.when.apply($, userLoungeCalls).done(function() {
            var template = $('#userLoungesTemplate').html();
            var rendered = Mustache.render(template, userLounges);
            $('#userLounges').html(rendered);
        }).fail(function() {
            loadUserLoungesError();
        })
    }).fail(function(picture, textStatus, jqXHR) {
        loadUserLoungesError();
    });
}

function loadUpcomingUserLounges() {
    var user = loadUserOrPreview();
    function loadUpcomingUserLoungesError() {
        $('#welcomeMessage').html(error('We couldn\'t load your upcoming lounges. Please refresh the page to try again.'));
        return;
    }

    $.ajax({
        type: 'GET',
        url: user.userLounges.href,
        data: 'time=future'
    }).done(function(userLounges, textStatus, jqXHR) {
        var userLoungeCalls = [];
       
        $.each(userLounges.items, function(index, userLounge) {
            // Populating the host attribute with the actual user info 
            userLoungeCalls.push(
                $.ajax({
                    type: 'GET',
                    url: userLounge.lounge.href
                }).done(function(lounge, textStatus, jqXHR) {
                    userLounge.lounge = lounge;
                    userLounge.lounge.dateTime = formatDateTime(userLounge.lounge.dateTime);
                }).fail(function(lounge, textStatus, jqXHR) {
                    loadUserLoungesError();
                })
            );
        });
         
        $.when.apply($, userLoungeCalls).done(function() {
            var template = $('#upcomingUserLoungesTemplate').html();
            var rendered = Mustache.render(template, userLounges);
            $('#upcomingUserLounges').html(rendered);
        }).fail(function() {
            loadUpcomingUserLoungesError();
        })
    }).fail(function(picture, textStatus, jqXHR) {
        loadUpcomingUserLoungesError();
    });
}

$('#upload-picture').on('change', '#upload-picture-file', function(event) {
    event.preventDefault();
    $('#upload-picture-form').submit(); 
})

$('#upload-picture').on('submit', '#upload-picture-form', function(event) {
    function uploadPictureError() {
        $('#picture-error').html(error('We couldn\'t upload your picture. Make sure it is a jpg, png, or gif file.'));
        return;
    }
    
    event.preventDefault();
    
    var user = loadUserOrPreview();
    var data = new FormData($('#upload-picture-form')[0]);
    $.ajax({
        type: 'POST',
        url: '/api/pictures/',
        data: data,
        contentType: false,
        cache: false,
        processData: false
    }).done(function(picture, textStatus, jqXHR) {
        user.picture = {
            'href': picture.href
        };
        $('#picture-error').hide()
        $.ajax({
            type: 'PUT',
            url: user.href,
            data: JSON.stringify(user),
            headers: getAuthentication(user),
            contentType: 'application/json'
        }).done(function(user) {
            refreshUser();
            loadPicture();
        }).fail(function(error, textStatus, jqXHR) {
            uploadPictureError();
        });
    }).fail(function(error, textStatus, jqXHR) {
        uploadPictureError();
    });
})

$('#delete-picture').on('submit', '#delete-picture-form', function(event) {
    function deletePictureError() {
        $('#picture-error').html(error('We couldn\'t delete your picture. Please refresh the page to try again.'));
        return;
    }
    
    event.preventDefault();
    
    var user = loadUserOrPreview();

    user.picture = {};

    $.ajax({
        type: 'PUT',
        url: user.href,
        data: JSON.stringify(user),
        headers: getAuthentication(user),
        contentType: 'application/json'
    }).done(function(user) {
        $('#picture-error').hide()
        refreshUser();
        loadPicture();
    }).fail(function(error, textStatus, jqXHR) {
        uploadPictureError();
    });
})

$('#editBio').click(function(event) {
    event.preventDefault();
    var user = loadUserOrPreview();
    var template = $('#bioEditTemplate').html();
    var rendered = Mustache.render(template, user);
    $('#bio').html(rendered);
})

$('#bio').on('submit', '#saveEditBioForm', function(event) {
    function saveBioError() {
        $('#bio').html(error('We couldn\'t save your bio. Please refresh the page to try again.'));
        return;
    }

    event.preventDefault();

    var user = loadUserOrPreview();
    user.bio = $('#editBioText').val()

    $.ajax({
        type: 'PUT',
        url: user.href,
        data: JSON.stringify(user),
        headers: getAuthentication(user),
        contentType: 'application/json'
    }).done(function(userLounges, textStatus, jqXHR) {
        loadBio();
    }).fail(function(picture, textStatus, jqXHR) {
        saveBioError();
    });
})

$('#bio').on('submit', '#cancelEditBioForm', function(event) {
    event.preventDefault();
    loadBio();
})

$('#hostApplicationForm').submit(function(event) {
    function hostApplicationError() {
        $('hostApplicationError').html(error('We couldn\'t submit your host application. Please refresh the page to try again.'));
        return;
    }

    function hostApplicationBadInputError() {
        $('hostApplicationError').html(error('There are some errors with your input (possibly length). Please fix them and try again.'));
        return;
    }

    function hostApplicationSuccess() {
        $('#hostApplicationError').html(success('We have submitted your application. Good luck!'));
        return;
    }

    event.preventDefault();
    var hostApplicationData = $('#hostApplicationForm').serializeObject();
    var user = loadUserOrPreview();

    $.ajax({
        type: 'POST',
        url: user.hostApplications.href,
        data: JSON.stringify(hostApplicationData),
        contentType: 'application/json',
        headers: getAuthentication(user)
    }).done(function(hostApplication, textStatus, jqXHR) {
        hostApplicationSuccess();
        $('#hostApplicationFormBtn').hide()
    }).fail(function(error, textStatus, jqXHR) {
        if (error.status == 400) {
            hostApplicationBadInputError();
        }
        else {
            hostApplicationError();
        }
    });
})

$('#account-modal-btn').click(function(event) {
    deserialize('account-form', globals.currentUser);    
})

$('#account-form').submit(function(event) {
    function editAccountError() {
        $('account-error').html(error('We couldn\'t update your account settings. Please refresh the page to try again.'));
        return;
    }

    event.preventDefault();

    $.get(globals.currentUser.href).then(function(user, textStatus, jqXHR) {
        user = $.extend(true, user, $('#account-form').serializeObject());
        $.ajax({
            type: 'PUT',
            url: globals.currentUser.href,
            data: JSON.stringify(user), 
            contentType: 'application/json',
            headers: getAuthentication(globals.currentUser)
        }).done(function(user, textStatus, jqXHR) {
            location.reload();
        }).fail(function(error, textStatus, jqXHR) {
            editAccountError(); 
        });
    });
})

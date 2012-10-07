// Depends on: 
//      jquery.cookie.js


/** GTRDropbox Object
 * 
 *  Args as OBJECT with members:
 *      callback_url (optional): where to get redirected after a successful dropbox login
 *      uuid (optional): uuid used when uploading a file
 *      herald (optional): function(msg) that displays status messages to user about what is going on.
 *      onsuccess (optional): function(response) function called after a successful upload { error, msg, url, expires } 
 */

GTRDropbox = function ( args ){  
        //load cookie
        this.callback_url = args.callback_url || null;
        this.uuid = args.uuid || null;
        this.herald = args.herald || function (){return;};
        this.onsuccess = args.onsuccess || function (){return;};
        this.dbox_session = $.cookie('dbox_session') //null if empty
        if (this.dbox_session){ //logged in
            this.logged = true;
            
            /* Was I created after a redirection where we need to finish upload without the user having to click the button ? */
            if ( $.cookie('dbox_need_verification') ){
                $.cookie('dbox_need_verification', null); //delete cookie
                resp = getSyncJSON("/ws/dropbox_callback/" + this.dbox_session);
                if (resp.error == 0){
                    this.logged = true;
                    this.herald("Connection established... Uploading File");
                    return this.upload(this.uuid);
                }
                // Error block
                this.herald("Error establishing connection.");
                //delete session on error
                $.cookie('dbox_session', null);
            }
        }
        
}

GTRDropbox.prototype = {
    /** hidden properties for metadata */
    cookie: null,
    logged: false,
    message: "",
    uuid: null,
    login: function(){
            /* Returns:
             *          0: Error, 1: Sucess
             */
            if (!this.logged){
                    //have nothing. Start from scratch
                    //1) create cookie
                    console.log("no cookie. Creating...");
                    if (this.callback_url){
                        resp  = getSyncJSON("/ws/dropbox_login", { 
                            callback: window.location.protocol + "//" + window.location.host + 
                                      this.callback_url                            
                        });
                    }
                    else {
                        this.message = "callback url not provided!";
                        this.herald(this.message);
                        return false;
                    }
                    $.cookie('dbox_session', resp.req_key, { path: '/' } );
                    $.cookie('dbox_need_verification', "1", { path: '/' } );

                    //2) redirect
                    window.location.href = resp.url;
                    return true; //never reached due to redirection above
            }
            else{
                    // I am connected (but will verify nonetheless).
                    resp  = getSyncJSON("/ws/dropbox_login", { req_key: this.dbox_session } );
                    return resp.state;  // 0: error , 1: success
            }
        },
    upload: function(uuid){
        if(!this.logged){
            this.login();
            return;
        }
        resp = $.ajax({ 
                type: "GET",
                dataType: "json",
                url: "/ws/dropbox_upload/" + uuid + "/" + this.dbox_session,
                context: this,
                success: function(data){ 
                    if (data.error == 1){
                        // delete cookie so that the user can try again
                        this.herald("Outdated session found.Please try again!");
                        console.log(data);
                        this.cleanup()
                    }
                    else{//success
                        //this.herald(data.msg);
                        this.onsuccess(data);
                    }
                },
                failure: function(){
                    this.cleanup();
                    this.herald("Upload failed!");
                }
        });
    },
    cleanup: function(){
            $.cookie('dbox_session',null);
            $.cookie('dbox_need_verification',null);
            this.logged = false;
    }
}



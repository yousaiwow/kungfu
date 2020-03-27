//
// Created by Keren Dong on 2020/3/27.
//

#include <kungfu/yijinjing/index/session.h>

using namespace kungfu::longfist::types;
using namespace kungfu::yijinjing;
using namespace kungfu::yijinjing::cache;
using namespace kungfu::yijinjing::data;
using namespace kungfu::yijinjing::journal;

namespace kungfu::yijinjing::index {
std::string get_index_db_file(yijinjing::io_device_ptr &io_device) {
  auto locator = io_device->get_locator();
  auto index_location = location::make_shared(mode::LIVE, category::SYSTEM, "journal", "index", locator);
  return locator->layout_file(index_location, layout::SQLITE, "index");
}

session_keeper::session_keeper(yijinjing::io_device_ptr io_device)
    : session_storage_(make_storage(get_index_db_file(io_device), longfist::SessionDataTypes)) {
  if (not session_storage_.sync_schema_simulate().empty()) {
    session_storage_.sync_schema();
  }
}

Session &session_keeper::open_session(const data::location_ptr &source_location, int64_t time) {
  if (live_sessions_.find(source_location->uid) == live_sessions_.end()) {
    Session session = {};
    session.location_uid = source_location->uid;
    session.category = source_location->category;
    session.group = source_location->group;
    session.name = source_location->name;
    session.mode = source_location->mode;
    live_sessions_.emplace(session.location_uid, session);
  }
  Session &session = live_sessions_.at(source_location->uid);
  session.begin_time = time;
  session_storage_.replace(session);
  return session;
}

Session &session_keeper::close_session(const data::location_ptr &source_location, int64_t time) {
  Session &session = live_sessions_.at(source_location->uid);
  session_storage_.replace(session);
  return session;
}

Session &session_keeper::update_session(uint32_t source, const frame_ptr& frame) {
  Session &session = live_sessions_.at(source);
  session.end_time = frame->gen_time();
  session.frame_count++;
  session.data_size += frame->frame_length();
  return session;
}

std::vector<Session> session_keeper::find_sessions(uint32_t source, int64_t from, int64_t to) {
  return session_storage_.get_all<Session>();
}
} // namespace kungfu::yijinjing::index